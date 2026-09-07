@echo off
REM Ejecuta la aplicacion en modo desarrollo en Windows.
REM Requiere Python 3.12 instalado y el entorno virtual creado (ver DESARROLLO.md).
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo No se encontro el entorno virtual .venv
    echo Ejecute primero: python -m venv .venv ^&^& .venv\Scripts\pip install -r requirements-dev.txt
    pause
    exit /b 1
)
".venv\Scripts\python.exe" run_dev.py
pause
