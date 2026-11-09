"""
Menús interactivos para la interfaz de usuario
"""
from .colors import Colores, colorear, negrita

def mostrar_menu_principal():
    """Muestra el menú principal de opciones"""
    print(f"\n{negrita('¿Qué deseas hacer con este libro?')}")
    print(f"{colorear('[C]', Colores.OKGREEN)} Continuar procesando")
    print(f"{colorear('[O]', Colores.WARNING)} Omitir archivo")
    print(f"{colorear('[V]', Colores.OKBLUE)} Ver metadatos completos")
    return input(f"{negrita('Opción: ')}").strip().lower()

def mostrar_menu_metadatos():
    """Muestra el menú para manejar metadatos encontrados"""
    print(f"\n{negrita('¿Cómo proceder con los metadatos encontrados?')}")
    print(f"{colorear('[S]', Colores.OKGREEN)} Usar nombre sugerido")
    print(f"{colorear('[E]', Colores.WARNING)} Editar datos manualmente")
    print(f"{colorear('[N]', Colores.FAIL)} Ingresar datos desde cero")
    print(f"{colorear('[V]', Colores.OKBLUE)} Ver metadatos completos")
    return input(f"{negrita('Opción: ')}").strip().lower()

def mostrar_menu_post_proceso():
    """Muestra el menú después de procesar un archivo"""
    print(f"\n{negrita('¿Qué deseas hacer ahora?')}")
    print(f"{colorear('[C]', Colores.OKGREEN)} Continuar con el siguiente archivo")
    print(f"{colorear('[V]', Colores.OKBLUE)} Ver metadatos actualizados")
    print(f"{colorear('[R]', Colores.WARNING)} Recorregir datos de este archivo")
    print(f"{colorear('[S]', Colores.FAIL)} Salir del programa")
    return input(f"{negrita('Opción: ')}").strip().lower()

def mostrar_menu_colision(nombre_ocupado, alternativo):
    """Pregunta qué hacer cuando el nombre nuevo ya lo usa otro archivo"""
    print(f"\n{colorear(f'⚠ Ya existe otro archivo llamado: {nombre_ocupado}', Colores.WARNING)}")
    print(f"{colorear('[A]', Colores.OKGREEN)} Guardar como: {alternativo}")
    print(f"{colorear('[E]', Colores.WARNING)} Editar los datos")
    print(f"{colorear('[O]', Colores.FAIL)} Omitir este archivo")
    return input(f"{negrita('Opción: ')}").strip().lower()

def confirmar_accion(mensaje):
    """Confirma una acción con el usuario"""
    respuesta = input(f"{colorear(f'{mensaje} (s/n): ', Colores.WARNING)}").strip().lower()
    return respuesta == 's'
