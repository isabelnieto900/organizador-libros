"""
Validadores para datos de entrada
"""
import os
from config.settings import EXTENSIONES_VALIDAS

def validar_carpeta(ruta):
    """Valida que la carpeta exista"""
    return os.path.exists(ruta) and os.path.isdir(ruta)

def validar_archivo_pdf(nombre_archivo):
    """Valida que el archivo sea un PDF"""
    return any(nombre_archivo.lower().endswith(ext) for ext in EXTENSIONES_VALIDAS)

def obtener_archivos_pdf(carpeta):
    """Obtiene todos los archivos PDF de una carpeta"""
    if not validar_carpeta(carpeta):
        return []
    
    archivos = os.listdir(carpeta)
    return [
        f for f in archivos
        if validar_archivo_pdf(f) and os.path.isfile(os.path.join(carpeta, f))
    ]

def validar_datos_libro(autor, titulo, año):
    """Valida que los datos del libro sean correctos"""
    return all([autor.strip(), titulo.strip(), año.strip()])
