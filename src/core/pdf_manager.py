"""
Gestión de archivos PDF y sus metadatos
"""
import os
import shutil
import tempfile
from datetime import datetime
from pypdf import PdfReader, PdfWriter
from ..utils.text_utils import validar_año


class PDFProtegidoError(Exception):
    """El PDF está cifrado y no se pueden reescribir sus metadatos"""


def leer_metadatos(ruta):
    """Lee los metadatos de un archivo PDF como un diccionario de textos"""
    metadatos = PdfReader(ruta).metadata
    if not metadatos:
        return {}
    # Indexar (en vez de usar .items()) resuelve las referencias indirectas
    return {clave: str(metadatos[clave]) for clave in metadatos}


def actualizar_metadatos(ruta, autor, titulo, año, edicion=''):
    """Actualiza los metadatos internos del PDF sin arriesgar el original.

    Se escribe un archivo temporal en la misma carpeta y luego se reemplaza el
    original de una sola vez: si algo falla a mitad, el libro queda intacto.
    """
    reader = PdfReader(ruta)
    if reader.is_encrypted:
        raise PDFProtegidoError("El PDF está protegido; no se modificaron sus metadatos")

    # clone_from conserva marcadores, enlaces y el resto de la estructura
    writer = PdfWriter(clone_from=reader)
    metadatos = {
        "/Author": autor,
        "/Title": titulo,
        "/ModDate": f"D:{datetime.now().strftime('%Y%m%d%H%M%S')}",
    }
    if edicion:
        metadatos["/Subject"] = f"Edición: {edicion}"
    if validar_año(año):
        metadatos["/CreationDate"] = f"D:{año}0101000000"
    writer.add_metadata(metadatos)

    descriptor, temporal = tempfile.mkstemp(
        prefix='.organizador-', suffix='.pdf.tmp', dir=os.path.dirname(ruta)
    )
    try:
        with os.fdopen(descriptor, 'wb') as salida:
            writer.write(salida)
        shutil.copymode(ruta, temporal)
        os.replace(temporal, ruta)
    except BaseException:
        if os.path.exists(temporal):
            os.unlink(temporal)
        raise
