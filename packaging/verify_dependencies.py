#!/usr/bin/env python3
"""Verifica que estén presentes todas las dependencias necesarias antes de
compilar la versión portátil. Se ejecuta como parte de build_portable.ps1,
pero también puede correrse manualmente:

    python packaging\\verify_dependencies.py

Sale con código 0 si todo está en orden, o 1 si falta algo, imprimiendo en
español qué falta y cómo resolverlo.
"""
from __future__ import annotations

import importlib
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

PAQUETES_REQUERIDOS = [
    "PySide6", "pytesseract", "cv2", "fitz", "PIL", "docx", "numpy",
]

PAQUETES_OPCIONALES = ["spellchecker", "win32com"]


def verificar_paquetes_python() -> list[str]:
    errores = []
    for paquete in PAQUETES_REQUERIDOS:
        try:
            importlib.import_module(paquete)
        except ImportError:
            errores.append(
                f"Falta el paquete de Python '{paquete}'. "
                f"Instale las dependencias con: pip install -r requirements.txt"
            )
    for paquete in PAQUETES_OPCIONALES:
        try:
            importlib.import_module(paquete)
        except ImportError:
            print(f"[Aviso] Paquete opcional no instalado: {paquete} (funcionalidad reducida, no crítico).")
    return errores


def verificar_tesseract_para_empaquetar() -> list[str]:
    errores = []
    carpeta_tesseract = RAIZ / "herramientas" / "tesseract_windows"
    exe = carpeta_tesseract / "tesseract.exe"
    tessdata_spa = carpeta_tesseract / "tessdata" / "spa.traineddata"
    if not exe.exists():
        errores.append(
            f"No se encontró {exe}. Coloque una copia de Tesseract OCR para "
            "Windows en esa ruta antes de compilar (ver docs/INSTALACION.md, "
            "sección 'Obtener Tesseract para Windows')."
        )
    if not tessdata_spa.exists():
        errores.append(
            f"No se encontró {tessdata_spa}. Falta el paquete de idioma "
            "español (spa.traineddata)."
        )
    return errores


def verificar_recursos() -> list[str]:
    errores = []
    if not (RAIZ / "resources" / "iconos" / "app.ico").exists():
        errores.append("Falta resources/iconos/app.ico (ícono del ejecutable).")
    if not (RAIZ / "resources" / "plantillas" / "Plantilla_Notarial.docx").exists():
        errores.append(
            "Falta resources/plantillas/Plantilla_Notarial.docx. "
            "Ejecute: python scripts/generar_ejemplos.py"
        )
    if not (RAIZ / "ejemplos").exists() or not any((RAIZ / "ejemplos").iterdir()):
        errores.append(
            "La carpeta ejemplos/ está vacía. Ejecute: python scripts/generar_ejemplos.py"
        )
    return errores


def verificar_pyinstaller() -> list[str]:
    if shutil.which("pyinstaller") is None:
        try:
            importlib.import_module("PyInstaller")
        except ImportError:
            return ["PyInstaller no está instalado. Instale con: pip install -r requirements-dev.txt"]
    return []


def main() -> int:
    todos_los_errores: list[str] = []
    todos_los_errores += verificar_paquetes_python()
    todos_los_errores += verificar_pyinstaller()
    todos_los_errores += verificar_recursos()

    if sys.platform == "win32":
        todos_los_errores += verificar_tesseract_para_empaquetar()
    else:
        print(
            "[Aviso] No se está en Windows: se omite la verificación de "
            "herramientas/tesseract_windows (solo aplica al compilar el .exe)."
        )

    if todos_los_errores:
        print("\nSe encontraron problemas antes de compilar:\n")
        for i, error in enumerate(todos_los_errores, 1):
            print(f"  {i}. {error}")
        return 1

    print("Todas las dependencias necesarias están presentes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
