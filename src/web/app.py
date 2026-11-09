"""
Versión web del organizador de libros PDF (Streamlit)

Se ejecuta con: streamlit run src/web/app.py
"""
import os
import sys

import streamlit as st

# Streamlit ejecuta este archivo como script suelto, no como parte del paquete src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.settings import CARPETA_LIBROS
from src.core.organizador import (
    Libro,
    aplicar_cambios,
    leer_libro,
    leer_metadatos,
    listar_libros,
    nombre_alternativo,
    nombre_ocupado,
    nombre_propuesto,
)
from src.utils.text_utils import limpiar_texto, validar_año
from src.utils.validators import validar_carpeta

PENDIENTE = 'Pendiente'
GUARDADO = 'Guardado'
OMITIDO = 'Omitido'
ERROR = 'Error'

CAMPOS = [
    ('autor', 'Autor'),
    ('titulo', 'Título'),
    ('año', 'Año'),
    ('edicion', 'Edición (opcional)'),
]

estado = st.session_state


# -----------------------------------------------------------------------------
# Datos
# -----------------------------------------------------------------------------

def cargar_carpeta(carpeta):
    """Lee todos los PDFs de la carpeta y reinicia la sesión"""
    rutas = listar_libros(carpeta)
    libros, estados, errores = [], [], []
    barra = st.progress(0.0, text='Leyendo PDFs…')
    for numero, ruta in enumerate(rutas, start=1):
        try:
            libros.append(leer_libro(ruta))
            estados.append(PENDIENTE)
            errores.append('')
        except Exception as e:
            libros.append(Libro(ruta))
            estados.append(ERROR)
            errores.append(str(e))
        barra.progress(numero / len(rutas), text=f'Leyendo {numero} de {len(rutas)}…')
    barra.empty()

    estado.carpeta_cargada = carpeta
    estado.libros = libros
    estado.estados = estados
    estado.errores = errores
    # Las claves de los campos llevan la generación para que, al recargar,
    # no se mezclen valores escritos para otro libro con el mismo índice
    estado.generacion = estado.get('generacion', 0) + 1
    estado.indice = 0
    estado.colision = None


def clave(campo):
    return f'{estado.generacion}_{estado.indice}_{campo}'


def faltan_datos(libro):
    return not limpiar_texto(libro.autor) or not limpiar_texto(libro.titulo)


def texto_propuesto(libro):
    return '(faltan autor o título)' if faltan_datos(libro) else nombre_propuesto(libro)


# -----------------------------------------------------------------------------
# Acciones (se ejecutan como callbacks, antes de redibujar la página)
# -----------------------------------------------------------------------------

def sincronizar_campos():
    """Copia lo escrito en el formulario al libro seleccionado"""
    libro = estado.libros[estado.indice]
    for campo, _ in CAMPOS:
        if clave(campo) in estado:
            setattr(libro, campo, estado[clave(campo)])


def al_editar():
    sincronizar_campos()
    if estado.estados[estado.indice] == GUARDADO:
        estado.estados[estado.indice] = PENDIENTE
    estado.colision = None


def ir_al_siguiente_pendiente():
    total = len(estado.libros)
    for paso in range(1, total + 1):
        siguiente = (estado.indice + paso) % total
        if estado.estados[siguiente] == PENDIENTE:
            estado.indice = siguiente
            return


def guardar(nombre=None):
    sincronizar_campos()
    estado.colision = None
    libro = estado.libros[estado.indice]
    if faltan_datos(libro):
        estado.mensaje = ('warning', 'El autor y el título son obligatorios.')
        return

    nombre = nombre or nombre_propuesto(libro)
    if nombre_ocupado(libro, nombre):
        estado.colision = {
            'indice': estado.indice,
            'nombre': nombre,
            'alternativo': nombre_alternativo(libro, nombre),
        }
        return

    nombre_anterior = libro.nombre_archivo
    try:
        resultado = aplicar_cambios(libro, nombre)
    except Exception as e:
        estado.mensaje = ('error', f'No se pudo guardar: {e}')
        return

    estado.estados[estado.indice] = GUARDADO
    if resultado.renombrado:
        texto = f'Renombrado: {nombre_anterior} → {libro.nombre_archivo}'
    else:
        texto = f'El nombre ya era correcto: {libro.nombre_archivo}'
    if resultado.metadatos_actualizados:
        estado.mensaje = ('success', texto)
    else:
        estado.mensaje = ('warning', f'{texto}. Metadatos sin cambios: {resultado.error_metadatos}')
    ir_al_siguiente_pendiente()


def omitir():
    estado.estados[estado.indice] = OMITIDO
    estado.colision = None
    ir_al_siguiente_pendiente()


def mover(paso):
    estado.indice = max(0, min(len(estado.libros) - 1, estado.indice + paso))
    estado.colision = None


def cancelar_colision():
    estado.colision = None


# -----------------------------------------------------------------------------
# Página
# -----------------------------------------------------------------------------

st.set_page_config(page_title='Organizador de libros PDF', page_icon='📚', layout='wide')
st.title('📚 Organizador de libros PDF')

with st.sidebar:
    carpeta = st.text_input('Carpeta de libros', value=CARPETA_LIBROS, key='carpeta').strip()
    recargar = st.button('Recargar', width='stretch')

if not carpeta:
    st.info('Escribe en la barra lateral la ruta de la carpeta con tus libros.')
    st.stop()
if not validar_carpeta(carpeta):
    st.error(f'La carpeta no existe: {carpeta}')
    st.stop()
if recargar or estado.get('carpeta_cargada') != carpeta:
    cargar_carpeta(carpeta)
if not estado.libros:
    st.warning('No se encontraron archivos PDF en la carpeta.')
    st.stop()

libros, estados, errores = estado.libros, estado.estados, estado.errores

with st.sidebar:
    st.divider()
    st.metric('PDFs', len(libros))
    st.caption(
        f'{estados.count(GUARDADO)} guardados · {estados.count(OMITIDO)} omitidos · '
        f'{estados.count(PENDIENTE)} pendientes · {estados.count(ERROR)} con error'
    )

if 'mensaje' in estado:
    tipo, texto = estado.pop('mensaje')
    getattr(st, tipo)(texto)

lista, formulario = st.columns([3, 2], gap='large')

with lista:
    st.dataframe(
        [
            {
                '': '▶' if numero == estado.indice else '',
                'Estado': estados[numero],
                'Nombre actual': libro.nombre_archivo,
                'Nombre propuesto': errores[numero] or (
                    libro.nombre_archivo if estados[numero] == GUARDADO else texto_propuesto(libro)
                ),
            }
            for numero, libro in enumerate(libros)
        ],
        hide_index=True,
        width='stretch',
        height=min(38 + 35 * len(libros), 600),
    )

with formulario:
    st.selectbox(
        'Libro',
        options=range(len(libros)),
        key='indice',
        format_func=lambda numero: f'{numero + 1}. {libros[numero].nombre_archivo}',
        on_change=cancelar_colision,
    )
    libro = libros[estado.indice]

    if estados[estado.indice] == ERROR:
        st.error(f'No se pudo leer el PDF: {errores[estado.indice]}')
    else:
        for campo, etiqueta in CAMPOS:
            st.text_input(etiqueta, value=getattr(libro, campo), key=clave(campo), on_change=al_editar)

        año = limpiar_texto(libro.año)
        if año and not validar_año(año):
            st.caption(f"⚠ '{año}' no es un año de 4 dígitos: irá en el nombre, pero no en los metadatos.")

        st.markdown('**Nombre nuevo:**')
        st.code(texto_propuesto(libro), language=None, wrap_lines=True)
        if texto_propuesto(libro) == libro.nombre_archivo:
            st.caption('(igual al actual)')

        colision = estado.colision
        if colision and colision['indice'] == estado.indice:
            st.warning(f"Ya existe otro archivo llamado **{colision['nombre']}**.")
            confirmar, cancelar = st.columns(2)
            confirmar.button(
                f"Guardar como «{colision['alternativo']}»",
                on_click=guardar,
                args=(colision['alternativo'],),
                width='stretch',
            )
            cancelar.button('Cancelar', on_click=cancelar_colision, width='stretch')

    botones = st.columns(4)
    botones[0].button(
        'Guardar', type='primary', on_click=guardar, width='stretch',
        disabled=estados[estado.indice] == ERROR,
    )
    botones[1].button(
        'Omitir', on_click=omitir, width='stretch',
        disabled=estados[estado.indice] == ERROR,
    )
    botones[2].button('◀ Anterior', on_click=mover, args=(-1,), width='stretch')
    botones[3].button('Siguiente ▶', on_click=mover, args=(1,), width='stretch')

    if estados[estado.indice] != ERROR:
        with st.expander('Ver metadatos'):
            try:
                metadatos = leer_metadatos(libro.ruta)
                if metadatos:
                    st.table([
                        {'Campo': clave_pdf.lstrip('/'), 'Valor': valor}
                        for clave_pdf, valor in metadatos.items()
                    ])
                else:
                    st.write('El archivo no tiene metadatos.')
            except Exception as e:
                st.error(f'No se pudieron leer los metadatos: {e}')
