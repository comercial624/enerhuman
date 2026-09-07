"""Preparación de imágenes antes del OCR.

Todas las funciones reciben y devuelven arreglos NumPy en formato OpenCV
(BGR o escala de grises) y son deliberadamente conservadoras: el objetivo es
mejorar la legibilidad para el OCR sin destruir trazos finos de letras,
números, sellos o firmas. El archivo original NUNCA se modifica; estas
funciones siempre trabajan sobre una copia en memoria o un archivo temporal.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import cv2

DPI_RECOMENDADO = 300
DPI_MINIMO_ACEPTABLE = 150


@dataclass
class ResultadoPreparacion:
    imagen: np.ndarray
    rotacion_aplicada_grados: float = 0.0
    inclinacion_corregida_grados: float = 0.0
    advertencias: list[str] = field(default_factory=list)


def calcular_dpi_efectivo(ancho_px: int, ancho_pulgadas: float) -> float:
    if ancho_pulgadas <= 0:
        return 0.0
    return ancho_px / ancho_pulgadas


def advertir_si_resolucion_baja(dpi_estimado: float) -> list[str]:
    if dpi_estimado and dpi_estimado < DPI_MINIMO_ACEPTABLE:
        return [
            f"La imagen tiene una resolución aproximada de {dpi_estimado:.0f} dpi, "
            f"por debajo de lo recomendado ({DPI_RECOMENDADO} dpi). "
            "El reconocimiento de texto puede contener más errores de lo habitual."
        ]
    return []


def a_escala_grises(imagen: np.ndarray) -> np.ndarray:
    if len(imagen.shape) == 2:
        return imagen
    return cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)


def detectar_angulo_inclinacion(gris: np.ndarray) -> float:
    """Estima el ángulo de inclinación (grados) usando la transformada de
    Hough sobre bordes, buscando líneas casi horizontales de texto/renglones.
    Devuelve 0.0 si no se puede estimar con confianza.
    """
    bordes = cv2.Canny(gris, 50, 150, apertureSize=3)
    lineas = cv2.HoughLines(bordes, 1, np.pi / 180, threshold=200)
    if lineas is None:
        return 0.0

    angulos = []
    for linea in lineas[:200]:
        rho, theta = linea[0]
        angulo_grados = (theta * 180 / np.pi) - 90
        if -20 <= angulo_grados <= 20:
            angulos.append(angulo_grados)

    if not angulos:
        return 0.0
    return float(np.median(angulos))


def corregir_inclinacion(imagen: np.ndarray, angulo: float) -> np.ndarray:
    if abs(angulo) < 0.1:
        return imagen
    (alto, ancho) = imagen.shape[:2]
    centro = (ancho // 2, alto // 2)
    matriz = cv2.getRotationMatrix2D(centro, angulo, 1.0)
    return cv2.warpAffine(
        imagen, matriz, (ancho, alto),
        flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE,
    )


def rotar_90(imagen: np.ndarray, grados: int) -> np.ndarray:
    """Rota la imagen en múltiplos de 90 grados (giro manual del usuario)."""
    grados = grados % 360
    if grados == 90:
        return cv2.rotate(imagen, cv2.ROTATE_90_CLOCKWISE)
    if grados == 180:
        return cv2.rotate(imagen, cv2.ROTATE_180)
    if grados == 270:
        return cv2.rotate(imagen, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return imagen


def eliminar_ruido_moderado(gris: np.ndarray) -> np.ndarray:
    """Reducción de ruido suave (no agresiva) para no borrar trazos finos."""
    return cv2.fastNlMeansDenoising(gris, h=7, templateWindowSize=7, searchWindowSize=21)


def corregir_sombras(gris: np.ndarray) -> np.ndarray:
    """Aplana iluminación desigual (sombras de encuadernación, doblez, etc.)
    dividiendo la imagen entre una versión muy desenfocada de sí misma.
    """
    fondo = cv2.GaussianBlur(gris, (0, 0), sigmaX=25)
    fondo = np.where(fondo == 0, 1, fondo)
    normalizada = cv2.divide(gris, fondo, scale=255)
    return normalizada


def mejorar_contraste(gris: np.ndarray) -> np.ndarray:
    """CLAHE: mejora el contraste local sin saturar zonas ya oscuras/claras."""
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gris)


def recortar_bordes(gris: np.ndarray, margen_px: int = 5) -> np.ndarray:
    """Recorta bordes en blanco/negro sobrantes del escaneo, con un margen
    de seguridad para no cortar texto pegado al borde.
    """
    _, binaria = cv2.threshold(gris, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    coords = cv2.findNonZero(binaria)
    if coords is None:
        return gris
    x, y, w, h = cv2.boundingRect(coords)
    alto, ancho = gris.shape[:2]
    x0 = max(0, x - margen_px)
    y0 = max(0, y - margen_px)
    x1 = min(ancho, x + w + margen_px)
    y1 = min(alto, y + h + margen_px)
    if (x1 - x0) < 10 or (y1 - y0) < 10:
        return gris
    return gris[y0:y1, x0:x1]


def aumentar_resolucion_si_insuficiente(gris: np.ndarray, dpi_estimado: float) -> np.ndarray:
    """Aumenta el tamaño (interpolación cúbica) cuando el escaneo es de baja
    resolución, para dar más píxeles por carácter al motor OCR.
    """
    if dpi_estimado and dpi_estimado < DPI_MINIMO_ACEPTABLE:
        factor = min(2.0, DPI_RECOMENDADO / max(dpi_estimado, 1))
        nuevo_ancho = int(gris.shape[1] * factor)
        nuevo_alto = int(gris.shape[0] * factor)
        return cv2.resize(gris, (nuevo_ancho, nuevo_alto), interpolation=cv2.INTER_CUBIC)
    return gris


def detectar_pagina_doble(gris: np.ndarray) -> bool:
    """Heurística simple: si hay una columna casi completamente oscura
    (línea de encuadernación) cerca del centro horizontal, se asume que la
    imagen contiene dos páginas escaneadas juntas.

    Se exige que la oscuridad cubra la mayor parte de la altura de la
    página (una línea continua), y no solo unas cuantas filas, para no
    confundir texto denso cerca del centro con una encuadernación real.
    """
    alto, ancho = gris.shape[:2]
    franja = gris[:, int(ancho * 0.4): int(ancho * 0.6)]
    if franja.size == 0:
        return False
    es_oscuro = franja < 100
    proporcion_oscura_por_columna = es_oscuro.mean(axis=0)
    return bool(np.max(proporcion_oscura_por_columna) > 0.85)


def separar_pagina_doble(gris: np.ndarray) -> list[np.ndarray]:
    ancho = gris.shape[1]
    mitad = ancho // 2
    return [gris[:, :mitad], gris[:, mitad:]]


def preparar_imagen(
    imagen_bgr: np.ndarray,
    dpi_estimado: float | None = None,
    auto_separar_paginas: bool = True,
) -> list[ResultadoPreparacion]:
    """Ejecuta el flujo completo de preparación sobre una página escaneada.

    Devuelve una lista de resultados: normalmente uno, pero dos si se separó
    una página doble.
    """
    gris = a_escala_grises(imagen_bgr)
    advertencias = advertir_si_resolucion_baja(dpi_estimado or 0.0)

    angulo = detectar_angulo_inclinacion(gris)
    gris = corregir_inclinacion(gris, angulo)

    gris = corregir_sombras(gris)
    gris = eliminar_ruido_moderado(gris)
    gris = mejorar_contraste(gris)
    gris = recortar_bordes(gris)

    if dpi_estimado:
        gris = aumentar_resolucion_si_insuficiente(gris, dpi_estimado)

    paginas = [gris]
    if auto_separar_paginas and detectar_pagina_doble(gris):
        paginas = separar_pagina_doble(gris)

    return [
        ResultadoPreparacion(
            imagen=pagina,
            inclinacion_corregida_grados=angulo,
            advertencias=list(advertencias),
        )
        for pagina in paginas
    ]
