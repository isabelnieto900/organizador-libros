"""
Utilidades para manejo de texto
"""
import re
from config.settings import CARACTERES_PROHIBIDOS, LONGITUD_MAXIMA_NOMBRE

def limpiar_texto(texto):
    """Limpia y normaliza texto para nombres de archivo"""
    if texto is None:
        return ''
    texto = str(texto)
    # 'Título: Subtítulo' -> 'Título - Subtítulo' (':' no se permite en Windows)
    texto = re.sub(r'\s*:\s*(?=\S)', ' - ', texto)
    texto = re.sub(CARACTERES_PROHIBIDOS, '', texto)
    # Saltos de línea, tabulaciones y otros caracteres de control (comunes en
    # los metadatos) se convierten en un solo espacio
    texto = re.sub(r'[\x00-\x1f\x7f\s]+', ' ', texto)
    return texto.strip()

def extraer_año_fecha(fecha):
    """Extrae el año de una fecha de metadatos"""
    if not fecha:
        return ''
    match = re.search(r'D:(\d{4})', fecha)
    return match.group(1) if match else ''

def extraer_edicion(asunto):
    """Extrae la edición del campo Subject escrito por este programa"""
    if not asunto:
        return ''
    match = re.match(r'\s*Edici[oó]n:\s*(.+)', str(asunto))
    return limpiar_texto(match.group(1)) if match else ''

def recortar_bytes(texto, maximo):
    """Recorta un texto para que ocupe como máximo `maximo` bytes en UTF-8"""
    codificado = texto.encode('utf-8')
    if len(codificado) <= maximo:
        return texto
    return codificado[:max(maximo, 0)].decode('utf-8', errors='ignore')

def generar_nombre_archivo(autor, titulo, año, edicion=None):
    """Genera un nombre de archivo estandarizado"""
    sufijo = ''
    if edicion and edicion.strip():  # Solo agrega edición si no está vacía
        sufijo += f' ({edicion.strip()} ed.)'
    if año and str(año).strip():
        sufijo += f' ({str(año).strip()})'
    sufijo += '.pdf'

    base = recortar_bytes(f'{autor} - {titulo}', LONGITUD_MAXIMA_NOMBRE - len(sufijo.encode('utf-8')))
    # Windows no acepta nombres terminados en punto o espacio, y al recortar
    # un título largo puede quedar uno al final
    return base.rstrip(' .') + sufijo

def validar_año(año):
    """Valida que el año sea un número de 4 dígitos"""
    if not año:
        return False
    return bool(re.match(r'^\d{4}$', str(año)))
