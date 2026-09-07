# -*- mode: python ; coding: utf-8 -*-
"""Especificación de PyInstaller para generar la versión portátil en modo
'onedir' (una carpeta con el .exe y todas sus dependencias al lado, sin
necesidad de instalar Python ni las librerías en la computadora del
cliente).

Ejecutar desde Windows, con el entorno virtual de desarrollo activado:

    pyinstaller packaging\TranscriptorNotarial.spec --noconfirm

El resultado queda en dist\TranscriptorNotarial\ (ver build_portable.bat,
que además arma la carpeta portátil completa con recursos, licencias,
ejemplos y manual).
"""
import sys
from pathlib import Path

RAIZ = Path(SPECPATH).resolve().parent  # packaging/ -> raíz del proyecto

block_cipher = None

a = Analysis(
    [str(RAIZ / "run_dev.py")],
    pathex=[str(RAIZ)],
    binaries=[],
    datas=[],
    hiddenimports=[
        "pytesseract",
        "docx",
        "PIL",
        "cv2",
        "fitz",
        "spellchecker",
        "win32com.client",
        "pythoncom",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="TranscriptorNotarial",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX puede disparar falsos positivos de antivirus; se evita.
    console=False,
    icon=str(RAIZ / "resources" / "iconos" / "app.ico"),
    version=str(RAIZ / "packaging" / "version_info.txt"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="TranscriptorNotarial",
)
