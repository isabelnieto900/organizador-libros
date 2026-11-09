"""
Pruebas unitarias para el organizador de libros
"""
import unittest
import os
import sys
import tempfile

from pypdf import PdfReader, PdfWriter

# Agregar el directorio raíz al path para las importaciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import organizador
from src.core.file_manager import ArchivoExistenteError, nombre_alternativo, renombrar_archivo
from src.core.pdf_manager import actualizar_metadatos, leer_metadatos
from src.utils.text_utils import (
    extraer_año_fecha,
    extraer_edicion,
    generar_nombre_archivo,
    limpiar_texto,
)
from src.utils.validators import validar_archivo_pdf, validar_datos_libro


def crear_pdf(ruta, paginas=3, metadatos=None):
    """Crea un PDF pequeño con páginas en blanco y un marcador"""
    writer = PdfWriter()
    for _ in range(paginas):
        writer.add_blank_page(width=200, height=200)
    writer.add_outline_item('Capítulo 1', 0)
    if metadatos:
        writer.add_metadata(metadatos)
    with open(ruta, 'wb') as salida:
        writer.write(salida)


class TestTextUtils(unittest.TestCase):
    """Pruebas para utilidades de texto"""
    
    def test_limpiar_texto(self):
        """Prueba la limpieza de texto"""
        self.assertEqual(limpiar_texto('Texto|Normal'), 'TextoNormal')
        self.assertEqual(limpiar_texto('Texto con "comillas"'), 'Texto con comillas')
        self.assertEqual(limpiar_texto(None), '')
        self.assertEqual(limpiar_texto('  Texto con espacios  '), 'Texto con espacios')

    def test_limpiar_texto_saltos_de_linea(self):
        """Los saltos de línea de los metadatos no llegan al nombre del archivo"""
        self.assertEqual(limpiar_texto('Cálculo\nen una\tvariable\r\n'), 'Cálculo en una variable')

    def test_limpiar_texto_subtitulo(self):
        """Los dos puntos de un subtítulo se convierten en guion"""
        self.assertEqual(limpiar_texto('Cálculo: trascendentes tempranas'), 'Cálculo - trascendentes tempranas')
    
    def test_extraer_año_fecha(self):
        """Prueba la extracción de año de fechas"""
        self.assertEqual(extraer_año_fecha('D:20230101120000'), '2023')
        self.assertEqual(extraer_año_fecha('D:19991231235959'), '1999')
        self.assertEqual(extraer_año_fecha(''), '')
        self.assertEqual(extraer_año_fecha(None), '')

    def test_extraer_edicion(self):
        """Prueba la lectura de la edición guardada en Subject"""
        self.assertEqual(extraer_edicion('Edición: 3'), '3')
        self.assertEqual(extraer_edicion('Un libro de física'), '')
        self.assertEqual(extraer_edicion(None), '')
    
    def test_generar_nombre_archivo(self):
        """Prueba la generación de nombres de archivo"""
        nombre = generar_nombre_archivo('García Márquez', 'Cien años de soledad', '1967')
        self.assertEqual(nombre, 'García Márquez - Cien años de soledad (1967).pdf')
        nombre = generar_nombre_archivo('Stewart', 'Cálculo', '2012', '7')
        self.assertEqual(nombre, 'Stewart - Cálculo (7 ed.) (2012).pdf')
        nombre = generar_nombre_archivo('Stewart', 'Cálculo', '')
        self.assertEqual(nombre, 'Stewart - Cálculo.pdf')

    def test_nombre_largo_se_recorta_sin_punto_ni_espacio_final(self):
        """Un título enorme cabe en 255 bytes y no deja '.' ni ' ' antes del sufijo"""
        titulo = 'Á' * 100 + ' y.' + 'x' * 300
        nombre = generar_nombre_archivo('Autor', titulo, '2020')
        self.assertLessEqual(len(nombre.encode('utf-8')), 255)
        self.assertTrue(nombre.endswith(' (2020).pdf'))

        # 'Autor - ' (8 bytes) + 117 'É' (234 bytes) + ' .' llega justo al límite
        # de 244 bytes que deja el sufijo ' (2020).pdf'
        nombre = generar_nombre_archivo('Autor', 'É' * 117 + ' .' + 'x' * 300, '2020')
        self.assertEqual(nombre, 'Autor - ' + 'É' * 117 + ' (2020).pdf')

class TestValidators(unittest.TestCase):
    """Pruebas para validadores"""
    
    def test_validar_archivo_pdf(self):
        """Prueba la validación de archivos PDF"""
        self.assertTrue(validar_archivo_pdf('libro.pdf'))
        self.assertTrue(validar_archivo_pdf('LIBRO.PDF'))
        self.assertFalse(validar_archivo_pdf('archivo.txt'))
        self.assertFalse(validar_archivo_pdf('imagen.jpg'))
    
    def test_validar_datos_libro(self):
        """Prueba la validación de datos de libro"""
        self.assertTrue(validar_datos_libro('Autor', 'Título', '2023'))
        self.assertFalse(validar_datos_libro('', 'Título', '2023'))
        self.assertFalse(validar_datos_libro('Autor', '', '2023'))
        self.assertFalse(validar_datos_libro('Autor', 'Título', ''))

class TestArchivos(unittest.TestCase):
    """Pruebas con archivos reales en una carpeta temporal"""

    def setUp(self):
        self._temporal = tempfile.TemporaryDirectory()
        self.carpeta = self._temporal.name

    def tearDown(self):
        self._temporal.cleanup()

    def ruta(self, nombre):
        return os.path.join(self.carpeta, nombre)

    def test_renombrar_no_sobrescribe(self):
        """En Linux os.rename pisaría el destino; aquí debe fallar sin tocar nada"""
        with open(self.ruta('a.pdf'), 'w') as f:
            f.write('A')
        with open(self.ruta('b.pdf'), 'w') as f:
            f.write('B')

        with self.assertRaises(ArchivoExistenteError):
            renombrar_archivo(self.ruta('a.pdf'), 'b.pdf')

        with open(self.ruta('a.pdf')) as f:
            self.assertEqual(f.read(), 'A')
        with open(self.ruta('b.pdf')) as f:
            self.assertEqual(f.read(), 'B')

    def test_nombre_alternativo(self):
        """Busca el primer sufijo libre"""
        for nombre in ('Libro (2020).pdf', 'Libro (2020) (2).pdf'):
            open(self.ruta(nombre), 'w').close()
        self.assertEqual(nombre_alternativo(self.carpeta, 'Libro (2020).pdf'), 'Libro (2020) (3).pdf')

    def test_actualizar_metadatos_conserva_paginas_y_marcadores(self):
        """Reescribir metadatos no pierde páginas ni índice ni deja temporales"""
        ruta = self.ruta('libro.pdf')
        crear_pdf(ruta, paginas=3, metadatos={'/Producer': 'Prueba'})

        actualizar_metadatos(ruta, 'Autora', 'Título', '1999', '2')

        reader = PdfReader(ruta)
        self.assertEqual(len(reader.pages), 3)
        self.assertEqual(len(reader.outline), 1)
        metadatos = leer_metadatos(ruta)
        self.assertEqual(metadatos['/Author'], 'Autora')
        self.assertEqual(metadatos['/Title'], 'Título')
        self.assertEqual(metadatos['/Subject'], 'Edición: 2')
        self.assertTrue(metadatos['/CreationDate'].startswith('D:1999'))
        self.assertEqual(os.listdir(self.carpeta), ['libro.pdf'])

    def test_año_invalido_no_se_escribe_en_metadatos(self):
        """'Desconocido_año' no debe producir una fecha inválida"""
        ruta = self.ruta('libro.pdf')
        crear_pdf(ruta, metadatos={'/CreationDate': 'D:20100101000000'})

        actualizar_metadatos(ruta, 'Autora', 'Título', 'Desconocido_año')

        self.assertEqual(leer_metadatos(ruta)['/CreationDate'], 'D:20100101000000')

    def test_aplicar_cambios_renombra_y_actualiza(self):
        """Flujo completo: leer, editar y aplicar"""
        crear_pdf(self.ruta('scan001.pdf'), metadatos={'/Author': 'Stewart', '/Title': 'Cálculo\n'})

        libro = organizador.leer_libro(self.ruta('scan001.pdf'))
        self.assertEqual((libro.autor, libro.titulo), ('Stewart', 'Cálculo'))
        libro.año = '2012'
        libro.edicion = '7'
        resultado = organizador.aplicar_cambios(libro)

        self.assertTrue(resultado.renombrado)
        self.assertTrue(resultado.metadatos_actualizados)
        self.assertEqual(libro.nombre_archivo, 'Stewart - Cálculo (7 ed.) (2012).pdf')
        self.assertEqual(os.listdir(self.carpeta), [libro.nombre_archivo])
        self.assertEqual(organizador.leer_libro(libro.ruta).edicion, '7')

    def test_aplicar_cambios_con_nombre_ocupado_no_toca_nada(self):
        """Si el destino existe, no se renombra ni se modifican metadatos"""
        crear_pdf(self.ruta('Autora - Libro (2000).pdf'))
        crear_pdf(self.ruta('otro.pdf'), metadatos={'/Author': 'Original'})

        libro = organizador.Libro(self.ruta('otro.pdf'), 'Autora', 'Libro', '2000')
        self.assertTrue(organizador.nombre_ocupado(libro))
        with self.assertRaises(ArchivoExistenteError):
            organizador.aplicar_cambios(libro)

        self.assertEqual(leer_metadatos(self.ruta('otro.pdf'))['/Author'], 'Original')
        self.assertEqual(
            organizador.nombre_alternativo(libro), 'Autora - Libro (2000) (2).pdf'
        )

if __name__ == '__main__':
    unittest.main()
