# Guía de desarrollo

## Requisitos

- Python 3.12 (recomendado; probado también con 3.11) de 64 bits.
- En Windows, para las funciones específicas: Microsoft Word instalado
  (para probar `word_integration.py`) y, opcionalmente, un escáner WIA
  (para `scanner_wia.py`).
- En Linux/macOS (usado para desarrollar la lógica de este repositorio):
  Tesseract OCR instalado del sistema (`apt install tesseract-ocr
  tesseract-ocr-spa` en Debian/Ubuntu) es suficiente para correr casi toda
  la suite de pruebas; los módulos exclusivos de Windows (COM de Word, WIA)
  degradan de forma segura y no rompen la importación.

## Instalación del entorno

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

## Ejecutar en modo desarrollo

```bash
python run_dev.py
```

En Linux sin entorno gráfico, use `QT_QPA_PLATFORM=offscreen python
run_dev.py` solo para verificar que la ventana se construye sin errores
(no verá nada en pantalla); para usar la aplicación de verdad hace falta
un entorno gráfico (Windows es el objetivo real).

## Ejecutar las pruebas

```bash
pytest tests/ -q
```

62 pruebas cubren: detección de entidades (regex), generación de Word,
persistencia de proyectos/sesión, resolución de rutas portátiles,
preprocesamiento de imagen, lectura de PDF/imágenes, el motor OCR contra
Tesseract real (se saltan automáticamente si Tesseract no está instalado)
y el pipeline completo de principio a fin (incluye cancelación y manejo de
errores por página).

Para ver cobertura:

```bash
pytest tests/ --cov=transcriptor_notarial --cov-report=term-missing
```

## Arquitectura

`transcriptor_notarial/core/` no importa nada de PySide6: es lógica de
negocio pura, testeable sin interfaz gráfica. `transcriptor_notarial/gui/`
consume `core/` y solo se encarga de presentación e hilos (`workers.py`
ejecuta `core/pipeline.py` en un `QThread` para no congelar la interfaz).

Flujo de una página, de principio a fin (`core/pipeline.py`):

1. `pdf_io.rasterizar_pagina` — convierte PDF/imagen a un arreglo BGR.
2. `pdf_io.extraer_texto_existente` — si el PDF ya trae texto, se usa
   directo (más confiable que el OCR).
3. `image_prep.preparar_imagen` — orientación, inclinación, sombras,
   ruido, contraste, recorte, aumento de resolución, separación de
   páginas dobles.
4. `ocr_engine.reconocer_pagina` — Tesseract en español; devuelve texto y
   palabras con coordenadas y confianza.
5. Todo se guarda incrementalmente en `core/project_store.Proyecto` vía
   `AlmacenProyectos`, para poder recuperar la sesión si la app se cierra.
6. En la revisión, `core/entities.detectar_entidades` resalta elementos
   relevantes (nunca los modifica).
7. `core/docx_export.generar_documento` produce el `.docx` final.
8. `core/word_integration.abrir_documento` lo abre en Word (COM, Windows).

## Convenciones

- Identificadores y mensajes de usuario en español; nombres de módulo y
  estructura de carpetas siguen convención Python estándar.
- Los módulos exclusivos de Windows (`word_integration.py`,
  `scanner_wia.py`) importan `pywin32` de forma protegida
  (`try/except ImportError`) para poder importarse en cualquier SO sin
  romper el resto de la aplicación ni la suite de pruebas.
- El registro técnico (`logging_setup.py`) tiene una lista cerrada de
  campos permitidos; no se debe pasar texto de documentos ni excepciones
  completas (`str(e)`) que puedan contener fragmentos del contenido — usar
  siempre `type(e).__name__` como `tipo_error`.

## Depuración

- Si Tesseract no se detecta en desarrollo, verifique
  `transcriptor_notarial.core.ocr_engine._detectar_tessdata_sistema()` — en
  Linux busca en rutas típicas (`/usr/share/tesseract-ocr/...`); en Windows
  usa `recursos\tesseract\tessdata` junto al ejecutable/script.
- Los archivos temporales de una sesión de desarrollo quedan en
  `~/.cache/TranscriptorNotarial` (Linux/macOS) o `%TEMP%\TranscriptorNotarial`
  (Windows); se pueden borrar sin riesgo entre pruebas.
- La configuración de desarrollo vive en
  `~/.local/share/TranscriptorNotarial` (Linux/macOS) o
  `%LOCALAPPDATA%\TranscriptorNotarial` (Windows).

## Generar la carpeta portátil y el manual

Ver `docs/INSTALACION.md` (requiere Windows para el `.exe` final).
`scripts/generar_ejemplos.py` y `scripts/generar_manual_pdf.py` sí corren
en cualquier SO y se usaron para producir `ejemplos/`,
`resources/plantillas/Plantilla_Notarial.docx` y `docs/Manual_de_Uso.pdf`
en este repositorio.
