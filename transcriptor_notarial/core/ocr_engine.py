"""Motor de reconocimiento óptico de caracteres (OCR) basado en Tesseract.

Busca el binario de Tesseract primero en la copia local portátil
(`recursos/tesseract/tesseract.exe`) y, si no existe, intenta usar una
instalación del sistema en el PATH. Nunca se contacta ningún servicio en
línea: todo el reconocimiento ocurre en el proceso local de Tesseract.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pytesseract
from pytesseract import Output

from .. import paths

IDIOMAS_SOPORTADOS = {
    "spa": "Español",
    "spa+eng": "Español e inglés",
    "eng": "Inglés",
}

# PSM 6: "Assume a single uniform block of text" — adecuado para actas y
# documentos legales con párrafos extensos y poca estructura de columnas.
CONFIG_SEGMENTACION_DOCUMENTO_LEGAL = "--psm 6"


class TesseractNoEncontradoError(Exception):
    pass


class IdiomaNoDisponibleError(Exception):
    pass


@dataclass
class PalabraReconocida:
    texto: str
    confianza: float  # 0-100
    x: int
    y: int
    ancho: int
    alto: int
    num_pagina: int
    num_parrafo: int
    num_linea: int

    @property
    def caja(self) -> tuple[int, int, int, int]:
        return (self.x, self.y, self.x + self.ancho, self.y + self.alto)


@dataclass
class ResultadoOCR:
    texto_completo: str
    palabras: list[PalabraReconocida] = field(default_factory=list)

    def palabras_baja_confianza(self, umbral: int) -> list[PalabraReconocida]:
        return [p for p in self.palabras if p.texto.strip() and p.confianza < umbral]


_CANDIDATOS_TESSDATA_SISTEMA = [
    "/usr/share/tesseract-ocr/5/tessdata",
    "/usr/share/tesseract-ocr/4.00/tessdata",
    "/usr/share/tessdata",
    "/usr/local/share/tessdata",
]


def _ruta_tesseract_portatil() -> Path | None:
    ruta = paths.tesseract_exe_path()
    return ruta if ruta.exists() else None


def _ruta_tesseract_sistema() -> str | None:
    return shutil.which("tesseract")


def _detectar_tessdata_sistema() -> Path | None:
    """Localiza la carpeta tessdata de una instalación del sistema.

    Orden de búsqueda: variable de entorno TESSDATA_PREFIX, rutas típicas de
    Linux (usadas al ejecutar las pruebas de este repositorio) y, en
    Windows, la subcarpeta 'tessdata' junto al ejecutable de Tesseract.
    """
    import os as _os
    prefijo = _os.environ.get("TESSDATA_PREFIX")
    if prefijo and Path(prefijo).exists():
        return Path(prefijo)

    for candidato in _CANDIDATOS_TESSDATA_SISTEMA:
        if Path(candidato).exists():
            return Path(candidato)

    ruta_sistema = _ruta_tesseract_sistema()
    if ruta_sistema:
        junto_al_binario = Path(ruta_sistema).resolve().parent / "tessdata"
        if junto_al_binario.exists():
            return junto_al_binario

    return None


def configurar_tesseract() -> Path | None:
    """Configura pytesseract para usar el binario disponible (portátil o
    del sistema). Devuelve la ruta de tessdata detectada, o None si no se
    pudo determinar de forma explícita (en ese caso se deja que el propio
    Tesseract use su carpeta de datos compilada por defecto).

    Lanza TesseractNoEncontradoError si no hay ningún binario disponible.
    """
    ruta_portatil = _ruta_tesseract_portatil()
    if ruta_portatil is not None:
        pytesseract.pytesseract.tesseract_cmd = str(ruta_portatil)
        return paths.tesseract_tessdata_dir()

    ruta_sistema = _ruta_tesseract_sistema()
    if ruta_sistema is not None:
        pytesseract.pytesseract.tesseract_cmd = ruta_sistema
        return _detectar_tessdata_sistema()

    raise TesseractNoEncontradoError(
        "No se encontró Tesseract OCR. Verifique que la carpeta "
        "'recursos\\tesseract' esté completa junto al programa, o que "
        "Tesseract esté instalado en el sistema."
    )


def verificar_idioma_disponible(idioma: str, tessdata_dir: Path | None) -> None:
    if tessdata_dir is None:
        # No se pudo determinar una carpeta explícita: se confía en la
        # configuración por defecto de Tesseract y el propio motor
        # reportará el error si el idioma no estuviera instalado.
        return
    codigos = idioma.split("+")
    faltantes = [c for c in codigos if not (tessdata_dir / f"{c}.traineddata").exists()]
    if faltantes:
        raise IdiomaNoDisponibleError(
            "No se encontró el paquete de idioma para: " + ", ".join(faltantes) +
            f". Verifique la carpeta {tessdata_dir}."
        )


def reconocer_pagina(
    imagen_gris: np.ndarray,
    idioma: str = "spa",
    num_pagina: int = 1,
    config_extra: str = CONFIG_SEGMENTACION_DOCUMENTO_LEGAL,
) -> ResultadoOCR:
    """Ejecuta OCR sobre una página ya preparada (imagen en escala de grises).

    Devuelve texto completo y el detalle palabra por palabra con coordenadas,
    confianza, número de línea y párrafo — todo obtenido directamente de
    Tesseract, sin ninguna corrección automática del contenido.
    """
    tessdata_dir = configurar_tesseract()
    verificar_idioma_disponible(idioma, tessdata_dir)

    prefijo_tessdata = f'--tessdata-dir "{tessdata_dir}" ' if tessdata_dir is not None else ""
    config = f'{prefijo_tessdata}-l {idioma} {config_extra}'

    texto_completo = pytesseract.image_to_string(imagen_gris, config=config)

    datos = pytesseract.image_to_data(
        imagen_gris, config=config, output_type=Output.DICT
    )

    palabras: list[PalabraReconocida] = []
    n = len(datos["text"])
    for i in range(n):
        texto = datos["text"][i]
        if texto is None or texto.strip() == "":
            continue
        confianza_raw = datos["conf"][i]
        try:
            confianza = float(confianza_raw)
        except (TypeError, ValueError):
            confianza = -1.0
        if confianza < 0:
            continue
        palabras.append(
            PalabraReconocida(
                texto=texto,
                confianza=confianza,
                x=int(datos["left"][i]),
                y=int(datos["top"][i]),
                ancho=int(datos["width"][i]),
                alto=int(datos["height"][i]),
                num_pagina=num_pagina,
                num_parrafo=int(datos["par_num"][i]),
                num_linea=int(datos["line_num"][i]),
            )
        )

    return ResultadoOCR(texto_completo=texto_completo, palabras=palabras)
