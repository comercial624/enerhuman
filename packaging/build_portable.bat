@echo off
REM Punto de entrada sencillo (doble clic) para generar la carpeta portátil.
REM Internamente llama a build_portable.ps1. Ver ese archivo para requisitos.
setlocal
cd /d "%~dp0\.."
powershell -ExecutionPolicy Bypass -File "packaging\build_portable.ps1"
pause
