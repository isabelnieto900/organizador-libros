"""
Funciones para mostrar información en consola
"""
from .colors import Colores, colorear, negrita

def imprimir_titulo(carpeta):
    """Imprime el título del programa"""
    print(f"\n{negrita(colorear('='*60, Colores.HEADER))}")
    print(negrita(colorear("📚 ORGANIZADOR DE LIBROS PDF 📚", Colores.HEADER)))
    print(f"{negrita(colorear('='*60, Colores.HEADER))}")
    print(f"{colorear(f'Organizando archivos en: {carpeta}', Colores.OKCYAN)}\n")

def imprimir_separador():
    """Imprime un separador visual"""
    print(f"{colorear('-'*60, Colores.OKBLUE)}")

def imprimir_exito(mensaje):
    """Imprime mensaje de éxito en verde"""
    print(f"{colorear(f'✓ {mensaje}', Colores.OKGREEN)}")

def imprimir_error(mensaje):
    """Imprime mensaje de error en rojo"""
    print(f"{colorear(f'✗ [ERROR] {mensaje}', Colores.FAIL)}")

def imprimir_info(mensaje):
    """Imprime mensaje informativo en azul"""
    print(f"{colorear(f'ℹ {mensaje}', Colores.OKBLUE)}")

def imprimir_advertencia(mensaje):
    """Imprime mensaje de advertencia en amarillo"""
    print(f"{colorear(f'⚠ {mensaje}', Colores.WARNING)}")

def mostrar_info_archivo(nombre, autor, titulo, año, edicion=None):
    """Muestra la información extraída del archivo de forma organizada"""
    print(f"\n{Colores.BOLD}{Colores.HEADER}📄 {nombre}{Colores.ENDC}")
    print(f"{Colores.OKBLUE}Autor:   {Colores.ENDC}{autor or f'{Colores.FAIL}NO ENCONTRADO{Colores.ENDC}'}")
    print(f"{Colores.OKBLUE}Título:  {Colores.ENDC}{titulo or f'{Colores.FAIL}NO ENCONTRADO{Colores.ENDC}'}")
    print(f"{Colores.OKBLUE}Edición: {Colores.ENDC}{edicion or f'{Colores.WARNING}NO ESPECIFICADA{Colores.ENDC}'}")
    print(f"{Colores.OKBLUE}Año:     {Colores.ENDC}{año or f'{Colores.FAIL}NO ENCONTRADO{Colores.ENDC}'}")

def mostrar_metadatos(metadatos):
    """Muestra los metadatos del PDF de forma organizada"""
    print(f"\n{negrita(colorear('📋 METADATOS DEL ARCHIVO', Colores.OKCYAN))}")
    print(f"{colorear('='*40, Colores.OKCYAN)}")

    if metadatos:
        for clave, valor in metadatos.items():
            clave_limpia = clave.replace('/', '').replace('_', ' ').title()
            print(f"{colorear(f'{clave_limpia:15}', Colores.OKBLUE)}: {valor}")
    else:
        imprimir_advertencia("No se encontraron metadatos en el archivo")

    print(f"{colorear('='*40, Colores.OKCYAN)}\n")

def mostrar_resumen_final(procesados, omitidos):
    """Muestra el resumen final del proceso"""
    print(f"\n{negrita(colorear('📊 RESUMEN FINAL', Colores.HEADER))}")
    print(f"{colorear(f'✓ Archivos procesados: {procesados}', Colores.OKGREEN)}")
    print(f"{colorear(f'⚠ Archivos omitidos: {omitidos}', Colores.WARNING)}")
    print(f"{negrita('🎉 ¡Proceso completado!')}\n")
