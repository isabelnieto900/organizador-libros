"""
Configuración principal del programa
"""
import os
from pathlib import Path
from dotenv import load_dotenv

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ_PROYECTO / '.env')

# Ruta de la carpeta de libros (definida en .env, ver .env.example)
CARPETA_LIBROS = os.path.expanduser(os.getenv('CARPETA_LIBROS', '').strip())

# Extensiones de archivo válidas
EXTENSIONES_VALIDAS = ['.pdf']

# Configuración de metadatos
METADATOS_REQUERIDOS = ['Author', 'Title', 'CreationDate']

# Caracteres prohibidos en nombres de archivo. Se usan los de Windows aunque
# el programa corra en Linux, porque los libros viven en OneDrive (NTFS).
CARACTERES_PROHIBIDOS = r'[\\/*?:"<>|]'

# Límite de ext4 y NTFS para el nombre de un archivo (en bytes UTF-8)
LONGITUD_MAXIMA_NOMBRE = 255

# Configuración de formato de nombres
FORMATO_NOMBRE = '{autor} - {titulo} ({año}).pdf'
