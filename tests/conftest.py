"""Utilidades comunes para las pruebas: generación de documentos ficticios
(sin datos personales reales) para probar el flujo de OCR y exportación.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

RUTA_FUENTE = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"

TEXTO_ACTA_FICTICIA = (
    "ESCRITURA NUMERO 12345\n\n"
    "En la ciudad de Guadalajara, Jalisco, siendo el dia 15 de marzo de 2024,\n"
    "ante mi, Licenciado Juan Perez Gonzalez, Notario Publico numero 10,\n"
    "comparecen los senores Maria Lopez Hernandez y Carlos Ramirez Torres,\n"
    "con domicilio en Calle Reforma numero 100, Colonia Centro, CP 44100,\n"
    "para celebrar el presente contrato por la cantidad de $50,000.00\n"
    "(cincuenta mil pesos 00/100 M.N.), con una superficie de 120.50 m2.\n"
)


@pytest.fixture()
def carpeta_temporal(tmp_path: Path) -> Path:
    return tmp_path


def crear_imagen_texto(
    texto: str,
    ruta_salida: Path,
    ancho: int = 1600,
    alto: int = 2000,
    tamano_fuente: int = 28,
    angulo_rotacion: float = 0.0,
) -> Path:
    """Genera una imagen PNG en blanco con texto renderizado, simulando una
    página escaneada, para usarla en pruebas de OCR sin datos reales.
    """
    imagen = Image.new("RGB", (ancho, alto), color="white")
    dibujo = ImageDraw.Draw(imagen)
    try:
        fuente = ImageFont.truetype(RUTA_FUENTE, tamano_fuente)
    except OSError:
        fuente = ImageFont.load_default()

    y = 150
    for linea in texto.split("\n"):
        dibujo.text((120, y), linea, fill="black", font=fuente)
        y += tamano_fuente + 20

    if angulo_rotacion:
        imagen = imagen.rotate(angulo_rotacion, fillcolor="white", expand=False)

    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    imagen.save(ruta_salida, dpi=(300, 300))
    return ruta_salida


def crear_pdf_desde_imagenes(rutas_imagenes: list[Path], ruta_salida: Path) -> Path:
    """Empaqueta una o más imágenes PNG/JPG en un PDF (simulando un PDF
    escaneado sin capa de texto).
    """
    import fitz  # PyMuPDF

    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    documento = fitz.open()
    for ruta_imagen in rutas_imagenes:
        imagen = Image.open(ruta_imagen)
        ancho_pt, alto_pt = imagen.width * 72 / 300, imagen.height * 72 / 300
        pagina = documento.new_page(width=ancho_pt, height=alto_pt)
        pagina.insert_image(pagina.rect, filename=str(ruta_imagen))
    documento.save(str(ruta_salida))
    documento.close()
    return ruta_salida


def crear_pdf_con_texto(texto: str, ruta_salida: Path) -> Path:
    """Genera un PDF que ya contiene una capa de texto real (no escaneado),
    para probar la ruta de extracción directa de texto sin OCR.
    """
    import fitz

    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    documento = fitz.open()
    pagina = documento.new_page()
    pagina.insert_text((72, 72), texto, fontsize=11)
    documento.save(str(ruta_salida))
    documento.close()
    return ruta_salida
