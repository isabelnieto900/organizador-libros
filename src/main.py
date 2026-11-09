"""
Programa principal del organizador de libros PDF (versión de terminal)
"""
import os
import sys

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import CARPETA_LIBROS
from .core.organizador import (
    ArchivoExistenteError,
    aplicar_cambios,
    leer_libro,
    leer_metadatos,
    listar_libros,
    nombre_alternativo,
    nombre_ocupado,
    nombre_propuesto,
)
from .ui.display import *
from .ui.menus import *
from .utils.validators import validar_carpeta
from .utils.text_utils import limpiar_texto

class OrganizadorLibros:
    """Clase principal del organizador de libros"""
    
    def __init__(self, carpeta):
        self.carpeta = carpeta
        self.archivos_procesados = 0
        self.archivos_omitidos = 0
    
    def obtener_datos_faltantes(self, campo, actual, archivo, requerido=True):
        """Solicita datos faltantes al usuario"""
        if actual:
            return actual
        
        while True:
            entrada = input(f"📝 [{archivo}] Ingresa {campo} (Enter para omitir): ").strip()
            
            if entrada:
                return limpiar_texto(entrada)
            
            # Si no es requerido, permitir campo vacío
            if not requerido:
                return ""
            
            # Si es requerido, preguntar si usar "Desconocido"
            if confirmar_accion(f"Campo vacío. ¿Usar 'Desconocido_{campo}'?"):
                return f'Desconocido_{campo}'
    
    def editar_datos(self, libro):
        """Permite corregir los datos del libro (Enter conserva el valor actual)"""
        libro.autor = input(f"Autor [{libro.autor}]: ").strip() or libro.autor
        libro.titulo = input(f"Título [{libro.titulo}]: ").strip() or libro.titulo
        libro.año = input(f"Año [{libro.año}]: ").strip() or libro.año
        libro.edicion = input(f"Edición [{libro.edicion}]: ").strip() or libro.edicion
    
    def ver_metadatos(self, ruta):
        """Muestra los metadatos del PDF o el error al leerlos"""
        try:
            mostrar_metadatos(leer_metadatos(ruta))
        except Exception as e:
            imprimir_error(f"No se pudieron leer los metadatos: {e}")
    
    def guardar(self, libro):
        """Aplica los cambios al libro. Devuelve False si el usuario lo omite"""
        nombre = nombre_propuesto(libro)
        while True:
            if nombre_ocupado(libro, nombre):
                alternativo = nombre_alternativo(libro, nombre)
                opcion = mostrar_menu_colision(nombre, alternativo)
                if opcion == 'a':
                    nombre = alternativo
                elif opcion == 'e':
                    self.editar_datos(libro)
                    nombre = nombre_propuesto(libro)
                    continue
                elif opcion == 'o':
                    imprimir_advertencia("Archivo omitido")
                    return False
                else:
                    imprimir_error("Opción no válida")
                    continue
            
            nombre_anterior = libro.nombre_archivo
            try:
                resultado = aplicar_cambios(libro, nombre)
            except ArchivoExistenteError:
                continue
            except Exception as e:
                imprimir_error(f"No se pudo guardar: {e}")
                return False
            
            if resultado.renombrado:
                imprimir_exito(f"Renombrado: {nombre_anterior} → {libro.nombre_archivo}")
            else:
                imprimir_info("El archivo ya tiene el nombre correcto")
            
            if resultado.metadatos_actualizados:
                imprimir_exito("Metadatos actualizados correctamente")
            else:
                imprimir_advertencia(f"Metadatos sin cambios: {resultado.error_metadatos}")
            return True
    
    def procesar_archivo(self, ruta):
        """Procesa un archivo PDF individual. Devuelve False para salir"""
        try:
            libro = leer_libro(ruta)
        except Exception as e:
            imprimir_error(f"{os.path.basename(ruta)}: {e}")
            return True  # Continúa automáticamente al siguiente archivo

        # Mostrar información del archivo
        mostrar_info_archivo(libro.nombre_archivo, libro.autor, libro.titulo, libro.año, libro.edicion)

        # Menú principal
        while True:
            decision = mostrar_menu_principal()

            if decision == 'o':
                imprimir_advertencia("Archivo omitido")
                self.archivos_omitidos += 1
                return True  # Continúa automáticamente al siguiente archivo
            elif decision == 'v':
                self.ver_metadatos(libro.ruta)
            elif decision == 'c':
                break
            else:
                imprimir_error("Opción no válida")
        
        # Procesar metadatos
        if libro.autor and libro.titulo and libro.año:
            print(f"\n💡 Nombre sugerido: {negrita(nombre_propuesto(libro))}")

            while True:
                usar = mostrar_menu_metadatos()

                if usar == 'v':
                    self.ver_metadatos(libro.ruta)
                elif usar == 'e':
                    self.editar_datos(libro)
                    break
                elif usar == 'n':
                    libro.autor = self.obtener_datos_faltantes('autor', '', libro.nombre_archivo)
                    libro.titulo = self.obtener_datos_faltantes('título', '', libro.nombre_archivo)
                    libro.año = self.obtener_datos_faltantes('año', '', libro.nombre_archivo)
                    libro.edicion = self.obtener_datos_faltantes('edición', '', libro.nombre_archivo, requerido=False)
                    break
                elif usar == 's':
                    break
                else:
                    imprimir_error("Opción no válida")
        else:
            imprimir_info("Completando datos faltantes...")
            libro.autor = self.obtener_datos_faltantes('autor', libro.autor, libro.nombre_archivo)
            libro.titulo = self.obtener_datos_faltantes('título', libro.titulo, libro.nombre_archivo)
            libro.año = self.obtener_datos_faltantes('año', libro.año, libro.nombre_archivo)
            libro.edicion = self.obtener_datos_faltantes('edición', libro.edicion, libro.nombre_archivo, requerido=False)

        if not self.guardar(libro):
            self.archivos_omitidos += 1
            return True

        self.archivos_procesados += 1

        # Menú post-proceso
        return self.manejar_post_proceso(libro)
    
    def manejar_post_proceso(self, libro):
        """Maneja las acciones después de procesar un archivo"""
        while True:
            post_accion = mostrar_menu_post_proceso()
            
            if post_accion == 'v':
                self.ver_metadatos(libro.ruta)
            elif post_accion == 'c':
                return True
            elif post_accion == 's':
                print(f"\n{negrita('👋 ¡Hasta luego!')}")
                return False
            elif post_accion == 'r':
                print(f"\n📝 Corrigiendo datos...")
                self.editar_datos(libro)
                if self.guardar(libro):
                    imprimir_exito("Datos corregidos")
            else:
                imprimir_error("Opción no válida")
    
    def ejecutar(self):
        """Ejecuta el programa principal"""
        if not self.carpeta:
            imprimir_error("No está definida CARPETA_LIBROS.")
            imprimir_info("Copia .env.example como .env (cp .env.example .env) y pon la ruta de tus libros.")
            return

        imprimir_titulo(self.carpeta)
        
        # Verificar carpeta
        if not validar_carpeta(self.carpeta):
            imprimir_error(f"La carpeta no existe: {self.carpeta}")
            return
        
        # Obtener archivos PDF
        archivos_pdf = listar_libros(self.carpeta)
        
        if not archivos_pdf:
            imprimir_advertencia("No se encontraron archivos PDF en la carpeta")
            return
        
        imprimir_info(f"Se encontraron {len(archivos_pdf)} archivos PDF para procesar")
        imprimir_separador()
        
        # Procesar archivos
        for ruta in archivos_pdf:
            if not self.procesar_archivo(ruta):
                break
            
            imprimir_separador()
        
        # Mostrar resumen
        mostrar_resumen_final(self.archivos_procesados, self.archivos_omitidos)

def main():
    """Función principal"""
    try:
        organizador = OrganizadorLibros(CARPETA_LIBROS)
        organizador.ejecutar()
    except (KeyboardInterrupt, EOFError):
        print(f"\n\n⚠ Proceso interrumpido por el usuario")
    except Exception as e:
        imprimir_error(f"Error inesperado: {e}")

if __name__ == "__main__":
    main()
