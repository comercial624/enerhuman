# Instalación, compilación y distribución (Windows)

Esta guía es para quien compila el programa, no para el usuario final (ver
`MANUAL_USUARIO.md` para eso). **Todo lo de este documento requiere una PC
con Windows 10/11 de 64 bits**; no puede hacerse desde Linux/macOS.

## 1. Preparar el entorno de desarrollo

```powershell
git clone <repositorio>
cd enerhuman
python -m venv .venv
.venv\Scripts\pip install --upgrade pip
.venv\Scripts\pip install -r requirements-dev.txt
```

Se recomienda Python 3.12 de 64 bits (python.org). Verifique con
`python --version`.

## 2. Obtener Tesseract OCR para Windows

El programa **no** depende de que Tesseract esté instalado en la
computadora del cliente: se incluye una copia dentro de la carpeta
portátil. Para prepararla en su máquina de desarrollo:

1. Descargue el instalador de Tesseract para Windows (build de UB Mannheim,
   ampliamente usado y de código abierto — verifique la licencia Apache 2.0
   en `licencias/`): busque "tesseract ocr windows installer UB Mannheim".
2. Instálelo en una carpeta cualquiera (por ejemplo `C:\tesseract-temp`),
   **marcando el componente de idioma español (`spa`)** en el instalador.
3. Copie el contenido de esa instalación (el ejecutable `tesseract.exe`,
   las DLL que lo acompañan y la carpeta `tessdata` con al menos
   `spa.traineddata` y `eng.traineddata`) a:

   ```
   herramientas\tesseract_windows\
     tesseract.exe
     *.dll
     tessdata\
       spa.traineddata
       eng.traineddata
       osd.traineddata
   ```

   Esta carpeta `herramientas\tesseract_windows` es solo para el proceso de
   compilación; `build_portable.ps1` la copia dentro de la carpeta
   portátil final como `recursos\tesseract`.
4. Revise la licencia de Tesseract (Apache 2.0) y del generador de
   instaladores que haya usado, y agregue sus avisos a `licencias/` si no
   están ya cubiertos por `licencias/LICENCIAS.md`.

## 3. Generar el ícono y la plantilla de ejemplo (si no existen)

```powershell
.venv\Scripts\python scripts\generar_ejemplos.py
```

Esto crea `resources\plantillas\Plantilla_Notarial.docx` y los archivos de
`ejemplos\`. El ícono `resources\iconos\app.ico` ya viene en el
repositorio; reemplácelo por el de su notaría si lo desea (mismo nombre y
formato .ico con varios tamaños).

## 4. Verificar dependencias antes de compilar

```powershell
.venv\Scripts\python packaging\verify_dependencies.py
```

Corrige cualquier problema que reporte antes de continuar.

## 5. Compilar la versión portátil

```powershell
powershell -ExecutionPolicy Bypass -File packaging\build_portable.ps1
```

Esto:
1. Corre `verify_dependencies.py`.
2. Compila con PyInstaller en modo `onedir` (`packaging\TranscriptorNotarial.spec`).
3. Arma `dist\Transcriptor_Notarial_Portable\` con el ejecutable, Tesseract,
   plantilla, iconos, ejemplos, licencias y `LEEME.txt`.
4. Genera el listado de archivos y hashes SHA-256
   (`dist\Transcriptor_Notarial_Portable_hashes_sha256.txt`).

Debe quedar con esta estructura (ver también la raíz del repositorio, que
ya trae `ejemplos/`, `licencias/`, `resources/` listos):

```
Transcriptor_Notarial_Portable\
  TranscriptorNotarial.exe
  LEEME.txt
  Manual_de_Uso.pdf
  VERSION.txt
  recursos\
    tesseract\
      tesseract.exe
      tessdata\spa.traineddata
    plantillas\Plantilla_Notarial.docx
    iconos\
  licencias\
  ejemplos\
```

### Generar el Manual_de_Uso.pdf

```powershell
.venv\Scripts\python scripts\generar_manual_pdf.py
```

Convierte `docs\MANUAL_USUARIO.md` a `docs\Manual_de_Uso.pdf`, que
`build_portable.ps1` copia a la carpeta portátil.

## 6. Comprimir a ZIP y calcular hashes finales

```powershell
Compress-Archive -Path "dist\Transcriptor_Notarial_Portable" -DestinationPath "dist\Transcriptor_Notarial_Portable.zip"
.venv\Scripts\python packaging\generate_hashes.py "dist\Transcriptor_Notarial_Portable" "dist\Transcriptor_Notarial_Portable.zip" "dist\TranscriptorNotarial\TranscriptorNotarial.exe"
```

## 7. Instalador opcional (Inno Setup)

Instale [Inno Setup 6](https://jrsoftware.org/isinfo.php) (código abierto,
licencia propia gratuita para este uso — ver `licencias/`) y compile:

```powershell
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" packaging\installer.iss
```

Genera `dist\TranscriptorNotarial_Instalador.exe`. Este instalador **no**
reemplaza la versión portátil: solo copia los mismos archivos a una
ubicación fija y crea accesos directos, para quien prefiera esa modalidad.

## 8. Copiar a una memoria USB

1. Conecte la memoria USB (formateada en NTFS o exFAT; FAT32 también sirve
   si ningún archivo supera 4 GB, lo cual es el caso normal aquí).
2. Copie la carpeta completa `Transcriptor_Notarial_Portable` a la raíz de
   la USB (o a la subcarpeta que prefiera).
3. Verifique que `TranscriptorNotarial.exe` esté presente antes de retirar
   la USB seguramente ("Expulsar hardware").

## 9. Ejecutar en la computadora del cliente

Ver `MANUAL_USUARIO.md`. En resumen: conectar la USB, abrir la carpeta,
doble clic en `TranscriptorNotarial.exe`. No requiere instalar nada, no
requiere Internet, no requiere permisos de administrador para el uso
normal.

## 10. Actualizar la versión portátil sin borrar documentos del usuario

Los documentos generados por el usuario **nunca** se guardan dentro de la
carpeta portátil (van a `Documentos\Transcripciones Notariales` en el
disco local, salvo que el usuario elija explícitamente otra carpeta). Por
lo tanto, para actualizar:

1. Genere la nueva carpeta portátil con los pasos anteriores.
2. En la USB, elimine la carpeta `Transcriptor_Notarial_Portable` anterior
   y copie la nueva en su lugar (o use una carpeta con el número de
   versión, p. ej. `Transcriptor_Notarial_Portable_v1.1`, y actualice el
   acceso directo si el usuario copió el programa localmente).
3. La configuración del usuario (`%LOCALAPPDATA%\TranscriptorNotarial`) es
   independiente de la carpeta portátil y no se pierde al reemplazarla.
4. Si el usuario usó "Copiar programa a esta computadora", repita esa
   copia desde la nueva versión portátil para actualizar también la copia
   local.

## 11. Pruebas de portabilidad pendientes (requieren Windows)

Ver `LIMITACIONES.md` para la lista completa de pruebas que deben
ejecutarse en una VM limpia de Windows 10 y otra de Windows 11 antes de
considerar esto listo para producción en la notaría (ejecución desde USB
con distintas letras de unidad, rutas con espacios/acentos, retiro
inesperado de la USB, Windows Defender activo, sin permisos de
administrador, etc.).
