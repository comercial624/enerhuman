"""Resolución de rutas para funcionamiento portátil.

Todas las rutas de la aplicación se calculan a partir de la ubicación real
del ejecutable (o del script, en modo desarrollo). Nunca se asume una letra
de unidad, un nombre de usuario ni una ruta fija de instalación, de modo que
el programa funcione igual si se ejecuta desde C:, D:, E:... o una memoria
USB con cualquier letra.
"""
from __future__ import annotations

import os
import sys
import string
import ctypes
from pathlib import Path

APP_NAME = "TranscriptorNotarial"


def is_frozen() -> bool:
    """True si el proceso corre como ejecutable compilado (PyInstaller)."""
    return getattr(sys, "frozen", False)


def app_base_dir() -> Path:
    """Carpeta base de la aplicación (donde vive el .exe o el código fuente).

    En modo compilado (PyInstaller onedir) es la carpeta que contiene el
    ejecutable. En modo desarrollo es la raíz del repositorio.
    """
    if is_frozen():
        return Path(sys.executable).resolve().parent
    # transcriptor_notarial/paths.py -> raíz del proyecto
    return Path(__file__).resolve().parent.parent


def resources_dir() -> Path:
    return app_base_dir() / "recursos"


def tesseract_exe_path() -> Path:
    return resources_dir() / "tesseract" / "tesseract.exe"


def tesseract_tessdata_dir() -> Path:
    return resources_dir() / "tesseract" / "tessdata"


def plantillas_dir() -> Path:
    return resources_dir() / "plantillas"


def iconos_dir() -> Path:
    return resources_dir() / "iconos"


def ejemplos_dir() -> Path:
    return app_base_dir() / "ejemplos"


def local_appdata_dir() -> Path:
    """Carpeta de configuración y temporales por usuario, fuera de la USB.

    En Windows: %LOCALAPPDATA%\\TranscriptorNotarial
    En otros sistemas (pruebas en Linux/macOS): ~/.local/share/TranscriptorNotarial
    """
    base = os.environ.get("LOCALAPPDATA")
    if base:
        return Path(base) / APP_NAME
    # Entorno de pruebas / desarrollo fuera de Windows.
    return Path.home() / ".local" / "share" / APP_NAME


def config_dir() -> Path:
    d = local_appdata_dir() / "config"
    d.mkdir(parents=True, exist_ok=True)
    return d


def config_file_path() -> Path:
    return config_dir() / "configuracion.json"


def app_local_copy_dir() -> Path:
    """Ruta sugerida para 'Copiar programa a esta computadora'."""
    return local_appdata_dir() / "App"


def temp_root_dir() -> Path:
    """Carpeta temporal de la app, fuera de la memoria USB por defecto."""
    base = os.environ.get("TEMP") or os.environ.get("TMP")
    if base:
        d = Path(base) / APP_NAME
    else:
        d = Path.home() / ".cache" / APP_NAME / "temp"
    d.mkdir(parents=True, exist_ok=True)
    return d


def default_output_dir() -> Path:
    """Carpeta de salida predeterminada para los documentos Word generados."""
    docs = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Documentos" / "Transcripciones Notariales"
    return docs


def logs_dir() -> Path:
    d = local_appdata_dir() / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def projects_dir() -> Path:
    """Carpeta local (no USB) donde se guardan sesiones de revisión / recuperación."""
    d = local_appdata_dir() / "proyectos"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _get_drive_type(drive_root: str) -> int:
    """Envuelve GetDriveTypeW de Windows. Devuelve -1 si no aplica (no Windows)."""
    if os.name != "nt":
        return -1
    try:
        return ctypes.windll.kernel32.GetDriveTypeW(ctypes.c_wchar_p(drive_root))
    except Exception:
        return -1


def is_running_from_removable_drive() -> bool:
    """Detecta si app_base_dir() está en una unidad extraíble (USB) en Windows.

    DRIVE_REMOVABLE = 2 según la API de Windows. En sistemas no Windows
    siempre devuelve False (usado en pruebas).
    """
    if os.name != "nt":
        return False
    base = app_base_dir()
    drive = base.drive  # p.ej. "D:"
    if not drive:
        return False
    drive_root = drive + "\\"
    DRIVE_REMOVABLE = 2
    return _get_drive_type(drive_root) == DRIVE_REMOVABLE


def available_drive_letters() -> list[str]:
    """Utilidad de diagnóstico: letras de unidad presentes (solo Windows)."""
    if os.name != "nt":
        return []
    letters = []
    for letter in string.ascii_uppercase:
        if os.path.exists(f"{letter}:\\"):
            letters.append(letter)
    return letters
