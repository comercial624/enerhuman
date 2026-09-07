"""Integración con Microsoft Word instalado localmente (solo Windows).

Se usa exclusivamente para ABRIR el documento .docx ya generado por
`docx_export.py` (que usa python-docx puro y no requiere Word). Word nunca
se utiliza para realizar el OCR ni para crear el contenido inicial.

Este módulo se importa de forma segura en cualquier sistema operativo: en
Linux/macOS (y en la suite de pruebas) las funciones lanzan
`WordNoDisponibleError` en lugar de fallar al importar, porque `pywin32`
solo existe en Windows.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

_PYWIN32_DISPONIBLE = False
if os.name == "nt":
    try:
        import win32com.client  # type: ignore
        import pythoncom  # type: ignore
        _PYWIN32_DISPONIBLE = True
    except ImportError:
        _PYWIN32_DISPONIBLE = False


class WordNoDisponibleError(Exception):
    pass


def word_esta_instalado() -> bool:
    """Detecta si Microsoft Word puede abrirse vía COM (solo Windows)."""
    if not _PYWIN32_DISPONIBLE:
        return False
    try:
        pythoncom.CoInitialize()
        try:
            word = win32com.client.Dispatch("Word.Application")
            word.Quit()
            return True
        finally:
            pythoncom.CoUninitialize()
    except Exception:
        return False


def abrir_documento(ruta_docx: Path) -> None:
    """Abre el documento en Microsoft Word.

    Si Word ya está abierto con otros documentos, se reutiliza esa
    instancia (no se cierran los demás documentos abiertos por el usuario).
    Si Word no está disponible, se intenta abrir con el programa
    predeterminado del sistema para archivos .docx como alternativa.
    """
    ruta_docx = Path(ruta_docx).resolve()
    if not ruta_docx.exists():
        raise FileNotFoundError(f"No se encontró el archivo a abrir: {ruta_docx}")

    if _PYWIN32_DISPONIBLE:
        try:
            pythoncom.CoInitialize()
            try:
                word = win32com.client.Dispatch("Word.Application")
                word.Visible = True
                # Reutiliza la instancia de Word si ya hay una abierta;
                # Dispatch (a diferencia de DispatchEx) se conecta a la
                # instancia existente cuando existe.
                word.Documents.Open(str(ruta_docx))
                return
            finally:
                pythoncom.CoUninitialize()
        except Exception as e:
            raise WordNoDisponibleError(
                "No se pudo abrir Microsoft Word automáticamente. "
                "Abra el archivo manualmente desde la carpeta de destino."
            ) from e

    # Sistemas sin pywin32 (o sin Windows): se intenta el asociador de
    # archivos del sistema operativo como respaldo razonable.
    try:
        os.startfile(str(ruta_docx))  # type: ignore[attr-defined]
    except AttributeError:
        try:
            subprocess.run(["xdg-open", str(ruta_docx)], check=False)
        except FileNotFoundError:
            raise WordNoDisponibleError(
                "No se encontró Microsoft Word ni un programa asociado para abrir .docx."
            )
