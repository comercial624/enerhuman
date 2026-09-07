# Encargo: compilar "Transcriptor Notarial" en Windows

Este documento es para la persona que compilará el programa. No necesita
saber programar, solo copiar y pegar comandos en PowerShell. Toma entre
15 y 30 minutos.

## Qué es esto

Un programa de escritorio (Transcriptor Notarial) que convierte actas
notariales escaneadas en documentos Word editables usando OCR local (sin
Internet, sin nube). El código ya está terminado y probado; solo falta
compilarlo en una PC con Windows porque el equipo donde se desarrolló es
Linux y no puede generar el `.exe` de Windows.

## Lo que necesitas

- Una PC con **Windows 10 o 11, de 64 bits**.
- Conexión a Internet (solo para descargar herramientas; el programa final
  no la necesita).
- Unos 2 GB libres en disco.
- No necesitas permisos de administrador para la mayoría de los pasos
  (solo quizá para instalar Python y Git si no están ya instalados).

## Paso 1 — Instalar Git y Python (si no los tienes)

- Git: https://git-scm.com/download/win (instalación con las opciones por defecto).
- Python 3.12 de 64 bits: https://www.python.org/downloads/ — **al instalar,
  marca la casilla "Add python.exe to PATH"**.

Verifica abriendo PowerShell y escribiendo:
```powershell
git --version
python --version
```
Ambos deben responder con un número de versión.

## Paso 2 — Descargar el código

En PowerShell:
```powershell
git clone https://github.com/comercial624/enerhuman.git
cd enerhuman
git checkout claude/ocr-notarial-documents-app-9pbumr
```

## Paso 3 — Preparar el entorno

```powershell
python -m venv .venv
.venv\Scripts\pip install --upgrade pip
.venv\Scripts\pip install -r requirements-dev.txt
```
Esto puede tardar varios minutos (descarga las librerías necesarias).

## Paso 4 — Descargar Tesseract OCR (el motor de reconocimiento de texto)

1. Ve a: https://github.com/UB-Mannheim/tesseract/wiki
2. Descarga el instalador de 64 bits más reciente (algo como
   `tesseract-ocr-w64-setup-5.x.x.exe`).
3. Ejecútalo. **Importante:** durante la instalación, en "Additional
   language data", marca **Spanish**.
4. Instálalo en la carpeta por defecto (normalmente
   `C:\Program Files\Tesseract-OCR`).
5. Copia el CONTENIDO de esa carpeta (no la carpeta en sí) a una nueva
   carpeta dentro del proyecto:
   ```powershell
   mkdir herramientas\tesseract_windows
   Copy-Item "C:\Program Files\Tesseract-OCR\*" "herramientas\tesseract_windows\" -Recurse
   ```
   Al final debe existir el archivo:
   `herramientas\tesseract_windows\tessdata\spa.traineddata`

## Paso 5 — Compilar

```powershell
powershell -ExecutionPolicy Bypass -File packaging\build_portable.ps1
```

Si todo sale bien, verás al final:
```
Listo. Carpeta portátil generada en: dist\Transcriptor_Notarial_Portable
```

Si el script se queja de algo antes de compilar, léelo con calma: te dice
en español exactamente qué falta (por ejemplo, si el Paso 4 quedó
incompleto).

## Paso 6 — Comprimir y devolver el resultado

```powershell
Compress-Archive -Path "dist\Transcriptor_Notarial_Portable" -DestinationPath "dist\Transcriptor_Notarial_Portable.zip"
```

Envía de vuelta el archivo `dist\Transcriptor_Notarial_Portable.zip`
(pésalo antes: puede rondar 150-250 MB por Tesseract incluido; usa
WeTransfer, Google Drive o similar si el correo lo rechaza por tamaño).

## Paso 7 (opcional pero recomendado) — Probar antes de enviar

Antes de comprimir, prueba que funcione:
1. Entra a `dist\Transcriptor_Notarial_Portable`.
2. Haz doble clic en `TranscriptorNotarial.exe`.
3. Prueba "Seleccionar PDF o imágenes" con algo de la carpeta `ejemplos\`
   del proyecto (son documentos ficticios, sin datos reales).
4. Presiona "Procesar documento" y verifica que reconozca el texto en
   español.

Si Windows muestra una advertencia de SmartScreen al abrir el .exe por
primera vez, es normal (el programa aún no tiene firma digital) — elige
"Más información" → "Ejecutar de todas formas". No es un virus.

## Si algo falla

Copia el mensaje de error exacto y devuélvelo junto con en qué paso
ocurrió. El archivo `docs\LIMITACIONES.md` y `docs\INSTALACION.md` dentro
del propio proyecto tienen más detalle técnico si hace falta.

## Qué hacer con el resultado una vez lo tengas

Una vez recibido el ZIP: descomprímelo, copia la carpeta
`Transcriptor_Notarial_Portable` completa a una memoria USB, y ya se
puede usar en la computadora de destino con doble clic en
`TranscriptorNotarial.exe` — no requiere instalar nada más ahí.
