# Genera la carpeta portátil completa "Transcriptor_Notarial_Portable".
#
# Requisitos para EJECUTAR ESTE SCRIPT (solo en la máquina de desarrollo,
# no en la computadora del cliente): Windows 10/11 de 64 bits, Python 3.12
# instalado, y haber creado el entorno virtual de desarrollo:
#
#   python -m venv .venv
#   .venv\Scripts\pip install -r requirements-dev.txt
#
# También debe existir una copia de Tesseract OCR para Windows en:
#   herramientas\tesseract_windows\   (ver docs\INSTALACION.md, sección
#   "Obtener Tesseract para Windows")
#
# Uso:
#   powershell -ExecutionPolicy Bypass -File packaging\build_portable.ps1

$ErrorActionPreference = "Stop"
$Raiz = Split-Path -Parent $PSScriptRoot
Set-Location $Raiz

Write-Host "== 1. Verificando dependencias =="
& ".venv\Scripts\python.exe" "packaging\verify_dependencies.py"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Verificación de dependencias fallida. Corrija los errores antes de continuar."
    exit 1
}

Write-Host "== 2. Compilando con PyInstaller (modo onedir) =="
& ".venv\Scripts\pyinstaller.exe" "packaging\TranscriptorNotarial.spec" --noconfirm --clean
if ($LASTEXITCODE -ne 0) {
    Write-Error "PyInstaller falló."
    exit 1
}

$CarpetaPortable = "dist\Transcriptor_Notarial_Portable"
if (Test-Path $CarpetaPortable) {
    Remove-Item -Recurse -Force $CarpetaPortable
}
New-Item -ItemType Directory -Path $CarpetaPortable | Out-Null

Write-Host "== 3. Copiando el ejecutable y sus dependencias =="
Copy-Item -Recurse "dist\TranscriptorNotarial\*" $CarpetaPortable

Write-Host "== 4. Copiando recursos (Tesseract, plantillas, iconos) =="
New-Item -ItemType Directory -Path "$CarpetaPortable\recursos" -Force | Out-Null

$TesseractOrigen = "herramientas\tesseract_windows"
if (-not (Test-Path $TesseractOrigen)) {
    Write-Warning "No se encontró $TesseractOrigen. Debe colocar ahí una copia de Tesseract OCR para Windows (con tessdata\spa.traineddata) antes de compilar. Ver docs\INSTALACION.md."
} else {
    Copy-Item -Recurse "$TesseractOrigen" "$CarpetaPortable\recursos\tesseract"
}

Copy-Item -Recurse "resources\plantillas" "$CarpetaPortable\recursos\plantillas"
Copy-Item -Recurse "resources\iconos" "$CarpetaPortable\recursos\iconos"

Write-Host "== 5. Copiando ejemplos, licencias y documentación =="
Copy-Item -Recurse "ejemplos" "$CarpetaPortable\ejemplos"
Copy-Item -Recurse "licencias" "$CarpetaPortable\licencias"
Copy-Item "docs\LEEME.txt" "$CarpetaPortable\LEEME.txt"
Copy-Item "VERSION.txt" "$CarpetaPortable\VERSION.txt"

if (Test-Path "docs\Manual_de_Uso.pdf") {
    Copy-Item "docs\Manual_de_Uso.pdf" "$CarpetaPortable\Manual_de_Uso.pdf"
} else {
    Write-Warning "No se encontró docs\Manual_de_Uso.pdf (generarlo desde docs\MANUAL_USUARIO.md, ver DESARROLLO.md)."
}

Write-Host "== 6. Generando listado de archivos y hashes =="
& ".venv\Scripts\python.exe" "packaging\generate_hashes.py" $CarpetaPortable

Write-Host ""
Write-Host "Listo. Carpeta portátil generada en: $CarpetaPortable"
Write-Host "Copie esa carpeta completa a la memoria USB."
