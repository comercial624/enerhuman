"""Lectura, unión y rasterización de PDF e imágenes de entrada.

Formatos soportados: PDF (con o sin texto), JPG, JPEG, PNG, TIFF de una o
varias páginas. El expediente de trabajo (posiblemente formado por varios
archivos de entrada) se representa como una lista ordenada de "páginas
fuente", cada una identificando su archivo de origen y número de página
dentro de ese archivo, para poder reordenarlas antes de procesar.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF
import numpy as np
from PIL import Image, ImageSequence

EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
EXTENSIONES_PDF = {".pdf"}
EXTENSIONES_SOPORTADAS = EXTENSIONES_IMAGEN | EXTENSIONES_PDF

DPI_RASTERIZACION = 300


class DocumentoProtegidoError(Exception):
    """El PDF requiere contraseña o tiene restricciones de lectura."""


class ArchivoDanadoError(Exception):
    """El archivo no pudo abrirse o está corrupto."""


@dataclass(frozen=True)
class PaginaFuente:
    archivo_origen: Path
    indice_pagina_en_archivo: int  # 0-based
    total_paginas_en_archivo: int

    @property
    def etiqueta(self) -> str:
        return f"{self.archivo_origen.name} (pág. {self.indice_pagina_en_archivo + 1}/{self.total_paginas_en_archivo})"


def contar_paginas(ruta: Path) -> int:
    ext = ruta.suffix.lower()
    if ext in EXTENSIONES_PDF:
        try:
            with fitz.open(ruta) as doc:
                if doc.needs_pass:
                    raise DocumentoProtegidoError(f"El archivo {ruta.name} requiere contraseña.")
                return doc.page_count
        except fitz.FileDataError as e:
            raise ArchivoDanadoError(f"El archivo {ruta.name} está dañado o no es un PDF válido.") from e
    elif ext in {".tif", ".tiff"}:
        try:
            with Image.open(ruta) as img:
                return sum(1 for _ in ImageSequence.Iterator(img))
        except Exception as e:
            raise ArchivoDanadoError(f"El archivo {ruta.name} está dañado.") from e
    elif ext in EXTENSIONES_IMAGEN:
        return 1
    raise ValueError(f"Extensión no soportada: {ext}")


def construir_expediente(rutas: list[Path]) -> list[PaginaFuente]:
    """Construye la lista ordenada de páginas fuente a partir de varios
    archivos seleccionados por el usuario, en el orden en que se pasaron.
    """
    paginas: list[PaginaFuente] = []
    for ruta in rutas:
        total = contar_paginas(ruta)
        for i in range(total):
            paginas.append(PaginaFuente(ruta, i, total))
    return paginas


def _pil_a_bgr(imagen_pil: Image.Image) -> np.ndarray:
    import cv2
    rgb = np.array(imagen_pil.convert("RGB"))
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def rasterizar_pagina(pagina: PaginaFuente, dpi: int = DPI_RASTERIZACION) -> tuple[np.ndarray, float]:
    """Convierte una página fuente (PDF o imagen) en un arreglo BGR de
    OpenCV, junto con el DPI efectivo estimado.

    Para PDF se rasteriza a `dpi`. Para imágenes ya rasterizadas, el DPI
    efectivo se calcula a partir de los metadatos si existen, o se asume
    `dpi` si no hay información disponible.
    """
    ext = pagina.archivo_origen.suffix.lower()

    if ext in EXTENSIONES_PDF:
        try:
            with fitz.open(pagina.archivo_origen) as doc:
                if doc.needs_pass:
                    raise DocumentoProtegidoError(
                        f"El archivo {pagina.archivo_origen.name} requiere contraseña."
                    )
                pag = doc.load_page(pagina.indice_pagina_en_archivo)
                zoom = dpi / 72.0
                matriz = fitz.Matrix(zoom, zoom)
                pix = pag.get_pixmap(matrix=matriz, colorspace=fitz.csRGB)
                imagen_pil = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                return _pil_a_bgr(imagen_pil), float(dpi)
        except fitz.FileDataError as e:
            raise ArchivoDanadoError(
                f"El archivo {pagina.archivo_origen.name} está dañado o no es un PDF válido."
            ) from e

    elif ext in {".tif", ".tiff"}:
        with Image.open(pagina.archivo_origen) as img:
            img.seek(pagina.indice_pagina_en_archivo)
            dpi_meta = img.info.get("dpi", (dpi, dpi))[0]
            return _pil_a_bgr(img), float(dpi_meta or dpi)

    elif ext in EXTENSIONES_IMAGEN:
        with Image.open(pagina.archivo_origen) as img:
            dpi_meta = img.info.get("dpi", (dpi, dpi))[0]
            return _pil_a_bgr(img), float(dpi_meta or dpi)

    raise ValueError(f"Extensión no soportada: {ext}")


def extraer_texto_existente(pagina: PaginaFuente) -> str | None:
    """Si la página proviene de un PDF que ya contiene una capa de texto,
    la devuelve directamente (más precisa que el OCR). Devuelve None si no
    hay texto embebido o el archivo no es PDF.
    """
    ext = pagina.archivo_origen.suffix.lower()
    if ext not in EXTENSIONES_PDF:
        return None
    try:
        with fitz.open(pagina.archivo_origen) as doc:
            pag = doc.load_page(pagina.indice_pagina_en_archivo)
            texto = pag.get_text("text")
            return texto if texto and texto.strip() else None
    except fitz.FileDataError:
        return None
