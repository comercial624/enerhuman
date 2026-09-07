"""Registro técnico con privacidad garantizada.

Reglas estrictas (ver README, sección Privacidad):
  - SÍ se guarda: fecha/hora, operación ejecutada, error técnico, duración,
    número de páginas.
  - NO se guarda jamás: texto de las actas, nombres, direcciones, imágenes,
    contenido reconocido ni ningún dato personal.

Por eso este módulo expone una función `registrar_evento` con una lista
cerrada de campos permitidos: no acepta texto libre de documentos ni
excepciones completas con datos incrustados (usar `tipo_error`, un código o
nombre de clase de excepción, nunca `str(excepcion)` si puede contener
fragmentos del documento).
"""
from __future__ import annotations

import logging
import re
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from . import paths

_logger: logging.Logger | None = None

# Se usa para blindar contra que, por error de programación, alguien pase
# una cadena larga (posible contenido de documento) como mensaje.
_LIMITE_CARACTERES_MENSAJE = 200


def _sanear(texto: str) -> str:
    texto = re.sub(r"\s+", " ", texto).strip()
    if len(texto) > _LIMITE_CARACTERES_MENSAJE:
        texto = texto[:_LIMITE_CARACTERES_MENSAJE] + "…(truncado)"
    return texto


def obtener_logger() -> logging.Logger:
    global _logger
    if _logger is not None:
        return _logger

    logger = logging.getLogger("transcriptor_notarial")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # `logging.getLogger` devuelve un objeto compartido en todo el proceso:
    # si `_logger` se reinició (por ejemplo tras `borrar_historial`, o en
    # pruebas que cambian de carpeta de datos), hay que quitar los
    # manejadores previos para no seguir escribiendo en una ruta anterior.
    for handler_previo in list(logger.handlers):
        logger.removeHandler(handler_previo)
        handler_previo.close()

    ruta_log = paths.logs_dir() / "tecnico.log"
    handler = RotatingFileHandler(
        ruta_log, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    formato = logging.Formatter("%(asctime)s\t%(levelname)s\t%(message)s")
    handler.setFormatter(formato)
    logger.addHandler(handler)

    _logger = logger
    return logger


def registrar_evento(
    operacion: str,
    duracion_segundos: float | None = None,
    num_paginas: int | None = None,
    tipo_error: str | None = None,
) -> None:
    """Registra un evento técnico sin ningún dato del contenido del documento.

    Parameters
    ----------
    operacion: nombre corto de la operación, p.ej. "procesar_documento",
        "exportar_word", "abrir_word". No debe incluir nombres de archivo
        con datos personales; usar descripciones genéricas.
    duracion_segundos: duración de la operación, si aplica.
    num_paginas: número de páginas procesadas, si aplica.
    tipo_error: nombre técnico del error (p.ej. "TesseractNoEncontrado"),
        nunca el texto completo de una excepción que pudiera contener
        fragmentos del documento.
    """
    logger = obtener_logger()
    partes = [f"operacion={_sanear(operacion)}"]
    if duracion_segundos is not None:
        partes.append(f"duracion_s={duracion_segundos:.2f}")
    if num_paginas is not None:
        partes.append(f"paginas={num_paginas}")
    if tipo_error:
        partes.append(f"error={_sanear(tipo_error)}")
    mensaje = " ".join(partes)
    if tipo_error:
        logger.error(mensaje)
    else:
        logger.info(mensaje)


def borrar_historial() -> None:
    """Elimina el historial técnico (opción de privacidad en Configuración)."""
    carpeta = paths.logs_dir()
    for archivo in carpeta.glob("tecnico.log*"):
        try:
            archivo.unlink()
        except OSError:
            pass
    global _logger
    if _logger is not None:
        for h in list(_logger.handlers):
            _logger.removeHandler(h)
            h.close()
        _logger = None
