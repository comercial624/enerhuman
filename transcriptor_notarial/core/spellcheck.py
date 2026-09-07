"""Corrector ortográfico de español, completamente local.

Usa `pyspellchecker`, cuyo diccionario se instala como datos del paquete
(no descarga nada en tiempo de ejecución ni envía texto a ningún servicio).
Si la librería no está disponible, el resto de la aplicación sigue
funcionando sin corrector ortográfico.
"""
from __future__ import annotations

import re

try:
    from spellchecker import SpellChecker
    _DISPONIBLE = True
except ImportError:
    _DISPONIBLE = False

_PATRON_PALABRA = re.compile(r"[A-Za-zÁÉÍÓÚÑÜáéíóúñü]+")

_instancia: "SpellChecker | None" = None


def disponible() -> bool:
    return _DISPONIBLE


def _obtener_instancia():
    global _instancia
    if _instancia is None and _DISPONIBLE:
        _instancia = SpellChecker(language="es")
    return _instancia


def palabras_mal_escritas(texto: str) -> set[str]:
    """Devuelve el conjunto de palabras que el corrector no reconoce.

    No corrige nada automáticamente: solo identifica candidatas para que el
    usuario decida. Los términos jurídicos, nombres propios y tecnicismos
    notariales pueden marcarse como "desconocidos" legítimamente; esto es
    solo una ayuda visual, no una corrección forzada.
    """
    revisor = _obtener_instancia()
    if revisor is None:
        return set()
    palabras = set(_PATRON_PALABRA.findall(texto))
    return revisor.unknown(palabras)


def sugerencias(palabra: str, maximo: int = 5) -> list[str]:
    revisor = _obtener_instancia()
    if revisor is None:
        return []
    candidatas = revisor.candidates(palabra) or set()
    return list(candidatas)[:maximo]
