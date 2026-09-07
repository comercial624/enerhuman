"""Configuración persistente de la aplicación.

Se guarda en JSON dentro de %LOCALAPPDATA%\\TranscriptorNotarial\\config
(fuera de la memoria USB), de modo que las preferencias del usuario
sobrevivan aunque la app se ejecute desde distintas unidades.
"""
from __future__ import annotations

import json
import dataclasses
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from . import paths


@dataclass
class ConfiguracionApp:
    # Carpetas
    carpeta_entrada_predeterminada: str = ""
    carpeta_salida_predeterminada: str = str(paths.default_output_dir())

    # Escáner
    escaner_predeterminado: str = ""
    resolucion_escaner_dpi: int = 300
    escaneo_color: bool = True  # True=color, False=escala de grises

    # OCR
    idioma_ocr: str = "spa"  # "spa", "spa+eng", u otro instalado
    umbral_baja_confianza: int = 85  # porcentaje 0-100

    # Word / documento de salida
    fuente_word: str = "Arial"
    tamano_letra: int = 12
    margen_superior_cm: float = 2.5
    margen_inferior_cm: float = 2.5
    margen_izquierdo_cm: float = 3.0
    margen_derecho_cm: float = 2.0
    interlineado: float = 1.15
    alineacion: str = "justificado"  # justificado, izquierda, centrado
    sangria_primera_linea_cm: float = 0.0
    numeracion_paginas: bool = False
    plantilla_word_predeterminada: str = ""

    # Comportamiento
    eliminar_temporales_al_cerrar: bool = True
    abrir_word_automaticamente: bool = True

    def a_diccionario(self) -> dict:
        return asdict(self)

    @staticmethod
    def desde_diccionario(datos: dict) -> "ConfiguracionApp":
        campos_validos = {f.name for f in dataclasses.fields(ConfiguracionApp)}
        filtrado = {k: v for k, v in datos.items() if k in campos_validos}
        return ConfiguracionApp(**filtrado)


class GestorConfiguracion:
    """Carga y guarda la configuración en disco de forma segura."""

    def __init__(self, ruta_archivo: Optional[Path] = None):
        self.ruta_archivo = ruta_archivo or paths.config_file_path()
        self._config = self._cargar()

    def _cargar(self) -> ConfiguracionApp:
        if self.ruta_archivo.exists():
            try:
                with open(self.ruta_archivo, "r", encoding="utf-8") as f:
                    datos = json.load(f)
                return ConfiguracionApp.desde_diccionario(datos)
            except (json.JSONDecodeError, OSError):
                # Configuración corrupta: se usan valores predeterminados.
                return ConfiguracionApp()
        return ConfiguracionApp()

    def guardar(self) -> None:
        self.ruta_archivo.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.ruta_archivo.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._config.a_diccionario(), f, ensure_ascii=False, indent=2)
        tmp.replace(self.ruta_archivo)

    @property
    def config(self) -> ConfiguracionApp:
        return self._config

    def actualizar(self, **cambios) -> None:
        for clave, valor in cambios.items():
            if hasattr(self._config, clave):
                setattr(self._config, clave, valor)
        self.guardar()

    def restaurar_predeterminados(self) -> None:
        self._config = ConfiguracionApp()
        self.guardar()
