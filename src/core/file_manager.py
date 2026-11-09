"""
Gestión de archivos y directorios
"""
import os


class ArchivoExistenteError(FileExistsError):
    """El nombre de destino ya pertenece a otro archivo"""

    def __init__(self, ruta_destino):
        super().__init__(f"Ya existe un archivo llamado '{os.path.basename(ruta_destino)}'")
        self.ruta_destino = ruta_destino


def ruta_destino(ruta_actual, nuevo_nombre):
    """Ruta que tendría el archivo con su nuevo nombre"""
    return os.path.join(os.path.dirname(ruta_actual), nuevo_nombre)


def destino_ocupado(ruta_actual, nuevo_nombre):
    """Indica si renombrar pisaría otro archivo distinto"""
    destino = ruta_destino(ruta_actual, nuevo_nombre)
    if destino == ruta_actual or not os.path.exists(destino):
        return False
    # En carpetas de Windows (sin distinción de mayúsculas), 'libro.pdf' y
    # 'Libro.pdf' son el mismo archivo y sí se puede renombrar
    return not os.path.samefile(ruta_actual, destino)


def renombrar_archivo(ruta_actual, nuevo_nombre):
    """Renombra un archivo sin sobrescribir otro y devuelve la nueva ruta.

    En Linux os.rename reemplaza el destino sin avisar, por eso se comprueba antes.
    """
    destino = ruta_destino(ruta_actual, nuevo_nombre)
    if destino == ruta_actual:
        return destino
    if destino_ocupado(ruta_actual, nuevo_nombre):
        raise ArchivoExistenteError(destino)
    os.rename(ruta_actual, destino)
    return destino


def nombre_alternativo(carpeta, nombre):
    """Devuelve 'nombre (2).pdf', 'nombre (3).pdf'... el primero que esté libre"""
    base, extension = os.path.splitext(nombre)
    contador = 2
    while True:
        candidato = f'{base} ({contador}){extension}'
        if not os.path.exists(os.path.join(carpeta, candidato)):
            return candidato
        contador += 1
