"""
Ventana del organizador de libros PDF (tkinter)
"""
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from config.settings import CARPETA_LIBROS
from ..core.organizador import (
    aplicar_cambios,
    leer_libro,
    leer_metadatos,
    listar_libros,
    nombre_alternativo,
    nombre_ocupado,
    nombre_propuesto,
)
from ..utils.text_utils import limpiar_texto, validar_año
from ..utils.validators import validar_carpeta

ESTADO_LEYENDO = 'Leyendo…'
ESTADO_PENDIENTE = 'Pendiente'
ESTADO_GUARDADO = 'Guardado'
ESTADO_OMITIDO = 'Omitido'
ESTADO_ERROR = 'Error'

CAMPOS = [
    ('autor', 'Autor'),
    ('titulo', 'Título'),
    ('año', 'Año'),
    ('edicion', 'Edición (opcional)'),
]


class VentanaOrganizador(tk.Tk):
    """Ventana principal: lista de PDFs a la izquierda, formulario a la derecha"""

    def __init__(self, carpeta):
        super().__init__()
        self.title('Organizador de libros PDF')
        ancho = min(1250, self.winfo_screenwidth() - 60)
        alto = min(650, self.winfo_screenheight() - 100)
        self.geometry(f'{ancho}x{alto}')
        self.minsize(850, 450)

        estilo = ttk.Style(self)
        if 'clam' in estilo.theme_names():
            estilo.theme_use('clam')

        self.libros = {}       # id de fila -> Libro
        self.errores = {}      # id de fila -> mensaje de error al leer
        self.seleccionado = None
        self.rellenando = False
        self.generacion = 0    # invalida cargas viejas al cambiar de carpeta

        self.carpeta = tk.StringVar(value=carpeta)
        self.campos = {campo: tk.StringVar() for campo, _ in CAMPOS}
        self.vista_previa = tk.StringVar()
        self.estado = tk.StringVar()

        self._construir()
        for variable in self.campos.values():
            variable.trace_add('write', self._al_editar)
        self.bind('<Control-s>', lambda evento: self.guardar())

        self.after(100, self.cargar_carpeta)

    # -------------------------------------------------------------------------
    # Construcción de la interfaz
    # -------------------------------------------------------------------------

    def _construir(self):
        barra = ttk.Frame(self, padding=(10, 10, 10, 0))
        barra.pack(fill='x')
        ttk.Label(barra, text='Carpeta:').pack(side='left')
        ttk.Entry(barra, textvariable=self.carpeta, state='readonly').pack(
            side='left', fill='x', expand=True, padx=6
        )
        ttk.Button(barra, text='Cambiar…', command=self.elegir_carpeta).pack(side='left')
        ttk.Button(barra, text='Recargar', command=self.cargar_carpeta).pack(side='left', padx=(6, 0))

        paneles = ttk.Panedwindow(self, orient='horizontal')
        paneles.pack(fill='both', expand=True, padx=10, pady=10)
        paneles.add(self._construir_lista(paneles), weight=3)
        paneles.add(self._construir_formulario(paneles), weight=2)

        ttk.Label(self, textvariable=self.estado, anchor='w', padding=(10, 0, 10, 8)).pack(fill='x')

    def _construir_lista(self, padre):
        marco = ttk.Frame(padre)
        columnas = ('estado', 'actual', 'propuesto')
        self.arbol = ttk.Treeview(marco, columns=columnas, show='headings', selectmode='browse')
        for columna, titulo, ancho in (
            ('estado', 'Estado', 90),
            ('actual', 'Nombre actual', 330),
            ('propuesto', 'Nombre propuesto', 330),
        ):
            self.arbol.heading(columna, text=titulo, anchor='w')
            self.arbol.column(columna, width=ancho, stretch=columna != 'estado')
        self.arbol.tag_configure(ESTADO_GUARDADO, foreground='#1a7f37')
        self.arbol.tag_configure(ESTADO_OMITIDO, foreground='#6e7781')
        self.arbol.tag_configure(ESTADO_ERROR, foreground='#cf222e')
        self.arbol.bind('<<TreeviewSelect>>', self._al_seleccionar)

        desplazamiento = ttk.Scrollbar(marco, orient='vertical', command=self.arbol.yview)
        self.arbol.configure(yscrollcommand=desplazamiento.set)
        self.arbol.pack(side='left', fill='both', expand=True)
        desplazamiento.pack(side='right', fill='y')
        return marco

    def _construir_formulario(self, padre):
        marco = ttk.Frame(padre, padding=(12, 0, 0, 0))
        marco.columnconfigure(1, weight=1)

        self.nombre_actual = ttk.Label(marco, font=('TkDefaultFont', 11, 'bold'))
        self.nombre_actual.grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 10))

        self.entradas = []
        for fila, (campo, etiqueta) in enumerate(CAMPOS, start=1):
            ttk.Label(marco, text=etiqueta).grid(row=fila, column=0, sticky='w', pady=3, padx=(0, 8))
            entrada = ttk.Entry(marco, textvariable=self.campos[campo])
            entrada.grid(row=fila, column=1, sticky='ew', pady=3)
            self.entradas.append(entrada)

        ttk.Label(marco, text='Nombre nuevo:').grid(row=5, column=0, columnspan=2, sticky='w', pady=(14, 2))
        etiqueta_vista_previa = ttk.Label(marco, textvariable=self.vista_previa, foreground='#0550ae')
        etiqueta_vista_previa.grid(row=6, column=0, columnspan=2, sticky='w')

        def ajustar_ancho_texto(evento):
            for etiqueta in (self.nombre_actual, etiqueta_vista_previa):
                etiqueta.configure(wraplength=max(evento.width - 20, 100))

        marco.bind('<Configure>', ajustar_ancho_texto)

        botones = ttk.Frame(marco)
        botones.grid(row=7, column=0, columnspan=2, sticky='ew', pady=(16, 0))
        botones.columnconfigure((0, 1), weight=1, uniform='botones')
        self.botones = [
            ttk.Button(botones, text='Guardar (Ctrl+S)', command=self.guardar),
            ttk.Button(botones, text='Omitir', command=self.omitir),
            ttk.Button(botones, text='Siguiente', command=self.siguiente),
            ttk.Button(botones, text='Ver metadatos', command=self.ver_metadatos),
        ]
        for posicion, boton in enumerate(self.botones):
            boton.grid(row=posicion // 2, column=posicion % 2, sticky='ew', padx=(0, 6), pady=(0, 6))

        self._habilitar_formulario(False)
        return marco

    def _habilitar_formulario(self, habilitado):
        for widget in self.entradas + self.botones:
            widget.state(['!disabled'] if habilitado else ['disabled'])

    # -------------------------------------------------------------------------
    # Carga de la carpeta
    # -------------------------------------------------------------------------

    def elegir_carpeta(self):
        inicial = self.carpeta.get() if validar_carpeta(self.carpeta.get()) else os.path.expanduser('~')
        carpeta = filedialog.askdirectory(parent=self, initialdir=inicial, mustexist=True)
        if carpeta:
            self.carpeta.set(carpeta)
            self.cargar_carpeta()

    def cargar_carpeta(self):
        self.generacion += 1
        self.arbol.delete(*self.arbol.get_children())
        self.libros.clear()
        self.errores.clear()
        self._mostrar_libro(None)

        carpeta = self.carpeta.get()
        if not carpeta:
            self.estado.set('No hay carpeta configurada en .env: elige una con «Cambiar…».')
            return
        if not validar_carpeta(carpeta):
            self.estado.set(f'La carpeta no existe: {carpeta}')
            return

        rutas = listar_libros(carpeta)
        if not rutas:
            self.estado.set('No se encontraron archivos PDF en la carpeta.')
            return

        filas = [
            (self.arbol.insert('', 'end', values=(ESTADO_LEYENDO, os.path.basename(ruta), '')), ruta)
            for ruta in rutas
        ]
        # Un PDF por ciclo de eventos, para que la ventana no se congele con
        # carpetas grandes (en /mnt/c la lectura es lenta)
        self.after(1, self._cargar_fila, filas, 0, self.generacion)

    def _cargar_fila(self, filas, indice, generacion):
        if generacion != self.generacion:
            return
        if indice >= len(filas):
            self._actualizar_resumen()
            return

        fila, ruta = filas[indice]
        self.estado.set(f'Leyendo {indice + 1} de {len(filas)}…')
        try:
            self.libros[fila] = leer_libro(ruta)
            self._marcar(fila, ESTADO_PENDIENTE)
        except Exception as e:
            self.errores[fila] = str(e)
            self.arbol.item(fila, values=(ESTADO_ERROR, os.path.basename(ruta), str(e)), tags=(ESTADO_ERROR,))

        if indice == 0:
            self._seleccionar(fila)
        self.after(1, self._cargar_fila, filas, indice + 1, generacion)

    # -------------------------------------------------------------------------
    # Selección y edición
    # -------------------------------------------------------------------------

    def _al_seleccionar(self, evento=None):
        seleccion = self.arbol.selection()
        self._mostrar_libro(seleccion[0] if seleccion else None)

    def _seleccionar(self, fila):
        self.arbol.selection_set(fila)
        self.arbol.focus(fila)
        self.arbol.see(fila)

    def _mostrar_libro(self, fila):
        self.seleccionado = fila
        libro = self.libros.get(fila)

        self.rellenando = True
        for campo, _ in CAMPOS:
            self.campos[campo].set(getattr(libro, campo) if libro else '')
        self.rellenando = False

        self._habilitar_formulario(libro is not None)
        if libro:
            self.nombre_actual.configure(text=libro.nombre_archivo)
            self._actualizar_vista_previa()
        elif fila in self.errores:
            self.nombre_actual.configure(text=self.arbol.set(fila, 'actual'))
            self.vista_previa.set(f'No se pudo leer el PDF: {self.errores[fila]}')
        else:
            self.nombre_actual.configure(text='')
            self.vista_previa.set('')

    def _al_editar(self, *argumentos):
        libro = self.libros.get(self.seleccionado)
        if self.rellenando or libro is None:
            return
        for campo, _ in CAMPOS:
            setattr(libro, campo, self.campos[campo].get())
        if self.arbol.set(self.seleccionado, 'estado') == ESTADO_GUARDADO:
            self._marcar(self.seleccionado, ESTADO_PENDIENTE)
        else:
            self.arbol.set(self.seleccionado, 'propuesto', self._texto_propuesto(libro))
        self._actualizar_vista_previa()

    def _faltan_datos(self, libro):
        return not limpiar_texto(libro.autor) or not limpiar_texto(libro.titulo)

    def _texto_propuesto(self, libro):
        return '(faltan autor o título)' if self._faltan_datos(libro) else nombre_propuesto(libro)

    def _actualizar_vista_previa(self):
        libro = self.libros[self.seleccionado]
        texto = self._texto_propuesto(libro)
        if texto == libro.nombre_archivo:
            texto += '\n(igual al actual)'
        self.vista_previa.set(texto)

    def _marcar(self, fila, estado):
        libro = self.libros[fila]
        propuesto = libro.nombre_archivo if estado == ESTADO_GUARDADO else self._texto_propuesto(libro)
        self.arbol.item(fila, values=(estado, libro.nombre_archivo, propuesto), tags=(estado,))

    # -------------------------------------------------------------------------
    # Acciones
    # -------------------------------------------------------------------------

    def guardar(self):
        libro = self.libros.get(self.seleccionado)
        if libro is None:
            return
        if self._faltan_datos(libro):
            messagebox.showwarning('Faltan datos', 'El autor y el título son obligatorios.', parent=self)
            return

        año = limpiar_texto(libro.año)
        if año and not validar_año(año):
            continuar = messagebox.askyesno(
                'Año poco común',
                f"'{año}' no es un año de 4 dígitos.\n"
                'Se usará en el nombre del archivo, pero no en los metadatos.\n\n¿Continuar?',
                parent=self,
            )
            if not continuar:
                return

        nombre = nombre_propuesto(libro)
        if nombre_ocupado(libro, nombre):
            alternativo = nombre_alternativo(libro, nombre)
            continuar = messagebox.askyesno(
                'Nombre ocupado',
                f'Ya existe otro archivo llamado:\n{nombre}\n\n¿Guardar este como?\n{alternativo}',
                parent=self,
            )
            if not continuar:
                return
            nombre = alternativo

        nombre_anterior = libro.nombre_archivo
        try:
            resultado = aplicar_cambios(libro, nombre)
        except Exception as e:
            messagebox.showerror('No se pudo guardar', str(e), parent=self)
            return

        self._marcar(self.seleccionado, ESTADO_GUARDADO)
        self.nombre_actual.configure(text=libro.nombre_archivo)
        if resultado.renombrado:
            mensaje = f'Renombrado: {nombre_anterior} → {libro.nombre_archivo}'
        else:
            mensaje = f'El nombre ya era correcto: {libro.nombre_archivo}'
        if not resultado.metadatos_actualizados:
            mensaje += ' (metadatos sin cambios)'
            messagebox.showwarning('Metadatos sin cambios', resultado.error_metadatos, parent=self)

        self._ir_al_siguiente_pendiente()
        self._actualizar_resumen(mensaje)

    def omitir(self):
        if self.seleccionado not in self.libros:
            return
        self._marcar(self.seleccionado, ESTADO_OMITIDO)
        self._ir_al_siguiente_pendiente()
        self._actualizar_resumen()

    def siguiente(self):
        if self.seleccionado is None:
            return
        proxima = self.arbol.next(self.seleccionado)
        if proxima:
            self._seleccionar(proxima)

    def _ir_al_siguiente_pendiente(self):
        filas = self.arbol.get_children()
        inicio = filas.index(self.seleccionado) + 1
        for fila in filas[inicio:] + filas[:inicio]:
            if self.arbol.set(fila, 'estado') == ESTADO_PENDIENTE:
                self._seleccionar(fila)
                return

    def ver_metadatos(self):
        libro = self.libros.get(self.seleccionado)
        if libro is None:
            return
        try:
            metadatos = leer_metadatos(libro.ruta)
        except Exception as e:
            messagebox.showerror('No se pudieron leer los metadatos', str(e), parent=self)
            return

        ventana = tk.Toplevel(self)
        ventana.title(f'Metadatos: {libro.nombre_archivo}')
        ventana.geometry('640x360')
        texto = tk.Text(ventana, wrap='word', padx=10, pady=10)
        texto.pack(fill='both', expand=True)
        if metadatos:
            for clave, valor in metadatos.items():
                texto.insert('end', f"{clave.lstrip('/')}: {valor}\n")
        else:
            texto.insert('end', 'El archivo no tiene metadatos.')
        texto.configure(state='disabled')
        ttk.Button(ventana, text='Cerrar', command=ventana.destroy).pack(pady=8)

    def _actualizar_resumen(self, mensaje=''):
        estados = [self.arbol.set(fila, 'estado') for fila in self.arbol.get_children()]
        resumen = (
            f'{len(estados)} PDFs · {estados.count(ESTADO_GUARDADO)} guardados · '
            f'{estados.count(ESTADO_OMITIDO)} omitidos · {estados.count(ESTADO_PENDIENTE)} pendientes'
        )
        if estados.count(ESTADO_ERROR):
            resumen += f' · {estados.count(ESTADO_ERROR)} con error'
        self.estado.set(f'{mensaje}   |   {resumen}' if mensaje else resumen)


def main():
    """Abre la ventana del organizador"""
    try:
        ventana = VentanaOrganizador(CARPETA_LIBROS)
    except tk.TclError as e:
        print(f'No se pudo abrir la ventana ({e}). En WSL hace falta WSLg o un servidor gráfico.')
        sys.exit(1)
    ventana.mainloop()
