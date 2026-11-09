"""
Lógica del organizador, compartida por la terminal y la ventana.

No imprime ni pide datos: devuelve resultados o lanza excepciones.
"""
import os
from dataclasses import dataclass
from typing import Optional

from . import file_manager, pdf_manager
from .file_manager import ArchivoExistenteError
from ..utils.text_utils import (
    extraer_año_fecha,
    extraer_edicion,
    generar_nombre_archivo,
    limpiar_texto,
)
from ..utils.validators import obtener_archivos_pdf


@dataclass
class Libro:
    """Un PDF con los datos que se usarán para nombrarlo"""
    ruta: str
    autor: str = ''
    titulo: str = ''
    año: str = ''
    edicion: str = ''

    @property
    def nombre_archivo(self):
        return os.path.basename(self.ruta)

    @property
    def carpeta(self):
        return os.path.dirname(self.ruta)


@dataclass
class ResultadoCambio:
    """Qué pasó al aplicar los cambios a un libro"""
    ruta: str
    renombrado: bool
    metadatos_actualizados: bool
    error_metadatos: Optional[str] = None


def listar_libros(carpeta):
    """Rutas de los PDFs de la carpeta, en orden alfabético"""
    nombres = sorted(obtener_archivos_pdf(carpeta), key=str.casefold)
    return [os.path.join(carpeta, nombre) for nombre in nombres]


def leer_libro(ruta):
    """Crea un Libro con los datos que trae el PDF en sus metadatos"""
    metadatos = pdf_manager.leer_metadatos(ruta)
    return Libro(
        ruta=ruta,
        autor=limpiar_texto(metadatos.get('/Author', '')),
        titulo=limpiar_texto(metadatos.get('/Title', '')),
        año=extraer_año_fecha(metadatos.get('/CreationDate', '')),
        edicion=extraer_edicion(metadatos.get('/Subject', '')),
    )


def leer_metadatos(ruta):
    """Todos los metadatos del PDF, para mostrarlos tal cual"""
    return pdf_manager.leer_metadatos(ruta)


def nombre_propuesto(libro):
    """Nombre de archivo que tendrá el libro con sus datos actuales"""
    return generar_nombre_archivo(
        limpiar_texto(libro.autor),
        limpiar_texto(libro.titulo),
        limpiar_texto(libro.año),
        limpiar_texto(libro.edicion),
    )


def nombre_ocupado(libro, nombre=None):
    """Indica si el nombre (por defecto, el propuesto) ya lo usa otro archivo"""
    return file_manager.destino_ocupado(libro.ruta, nombre or nombre_propuesto(libro))


def nombre_alternativo(libro, nombre=None):
    """Variante libre del nombre: 'Autor - Título (2020) (2).pdf'"""
    return file_manager.nombre_alternativo(libro.carpeta, nombre or nombre_propuesto(libro))


def aplicar_cambios(libro, nombre=None):
    """Actualiza los metadatos del PDF y lo renombra.

    Si el nombre ya lo usa otro archivo lanza ArchivoExistenteError antes de
    tocar nada. Un fallo al escribir los metadatos (por ejemplo, un PDF
    protegido) no impide el renombrado: queda indicado en el resultado.
    Al terminar, libro.ruta apunta al archivo renombrado.
    """
    nombre = nombre or nombre_propuesto(libro)
    if file_manager.destino_ocupado(libro.ruta, nombre):
        raise ArchivoExistenteError(file_manager.ruta_destino(libro.ruta, nombre))

    error_metadatos = None
    try:
        pdf_manager.actualizar_metadatos(
            libro.ruta,
            limpiar_texto(libro.autor),
            limpiar_texto(libro.titulo),
            limpiar_texto(libro.año),
            limpiar_texto(libro.edicion),
        )
    except Exception as e:
        error_metadatos = str(e)

    ruta_anterior = libro.ruta
    libro.ruta = file_manager.renombrar_archivo(libro.ruta, nombre)
    return ResultadoCambio(
        ruta=libro.ruta,
        renombrado=libro.ruta != ruta_anterior,
        metadatos_actualizados=error_metadatos is None,
        error_metadatos=error_metadatos,
    )
