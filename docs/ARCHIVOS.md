# Lista de archivos creados y su función

## Raíz del proyecto

| Archivo | Función |
|---|---|
| `README.md` | Punto de entrada de la documentación: qué es, estado real del entregable, inicio rápido. |
| `VERSION.txt` | Versión del programa, incluido dentro de la carpeta portátil. |
| `requirements.txt` | Dependencias de producción con versión fijada. |
| `requirements-dev.txt` | Dependencias adicionales para desarrollo (pytest, PyInstaller, reportlab). |
| `run_dev.py` / `run_dev.bat` | Ejecutan la aplicación sin compilar (modo desarrollo). |
| `.gitignore` | Excluye archivos generados (`__pycache__`, `.venv`, `dist/`, `build/`, `herramientas/`). |

## `transcriptor_notarial/` — código fuente de la aplicación

| Archivo | Función |
|---|---|
| `__init__.py` | Marca el paquete y define `__version__`. |
| `__main__.py` | Permite ejecutar con `python -m transcriptor_notarial`. |
| `app.py` | Punto de entrada: crea la `QApplication`, verifica Tesseract y abre la ventana principal. |
| `config.py` | `ConfiguracionApp` (valores) y `GestorConfiguracion` (carga/guardado en JSON, fuera de la USB). |
| `paths.py` | Toda la resolución de rutas portátiles: ubicación del ejecutable, recursos, temporales, detección de unidad extraíble. Sin esto el programa dependería de una letra de unidad fija. |
| `logging_setup.py` | Registro técnico con lista cerrada de campos permitidos (nunca contenido de documentos). |

### `transcriptor_notarial/core/` — lógica de negocio (sin GUI)

| Archivo | Función |
|---|---|
| `pdf_io.py` | Lee PDF/imágenes, cuenta páginas, arma el expediente combinando varios archivos, rasteriza a imagen, extrae texto ya existente en PDF. |
| `image_prep.py` | Preprocesamiento: escala de grises, inclinación, sombras, ruido, contraste, recorte, aumento de resolución, separación de páginas dobles. |
| `ocr_engine.py` | Configura y ejecuta Tesseract (portátil o del sistema); devuelve texto, palabras, coordenadas y confianza. |
| `entities.py` | Expresiones regulares para resaltar nombres, fechas, cantidades, folios, domicilios, CP, claves catastrales, etc. Nunca modifica el texto. |
| `docx_export.py` | Genera el `.docx` final (limpio o con plantilla), aplicando fuente, márgenes, interlineado, tablas y numeración configurados. |
| `project_store.py` | Guarda/recupera el proyecto de revisión (texto, correcciones, coordenadas, estado) para recuperación de sesión. |
| `pipeline.py` | Orquesta el procesamiento de todas las páginas de un expediente: progreso, cancelación, continuar tras error en una página, guardado incremental. |
| `word_integration.py` | Abre el `.docx` en Microsoft Word vía COM (solo Windows; degrada de forma segura en otros sistemas). |
| `scanner_wia.py` | Escaneo directo con WIA (solo Windows; módulo independiente y opcional). |
| `spellcheck.py` | Corrector ortográfico local en español (`pyspellchecker`), sin conexión a Internet. |

### `transcriptor_notarial/gui/` — interfaz PySide6

| Archivo | Función |
|---|---|
| `main_window.py` | Ventana principal: los 10 botones pedidos, barra de progreso, lista de páginas, menú de configuración y "copiar programa localmente". |
| `review_view.py` | Vista de revisión de dos paneles (imagen + texto), navegación de páginas, buscar/reemplazar, leyendas `[FIRMA]`/`[SELLO]`/etc. |
| `workers.py` | `QThread` que ejecuta `core.pipeline` en segundo plano sin congelar la interfaz. |
| `config_dialog.py` | Cuadro de diálogo de configuración (carpetas, escáner, OCR, Word, privacidad). |
| `widgets/image_viewer.py` | Visor de imagen: zoom, desplazamiento, giro, resaltado de la ubicación de una palabra dudosa. |
| `widgets/text_editor.py` | Editor de texto: resaltado de baja confianza y entidades, deshacer/rehacer, marcar palabra como revisada. |

## `tests/` — pruebas automatizadas (62 pruebas, `pytest tests/ -q`)

| Archivo | Cubre |
|---|---|
| `conftest.py` | Generación de imágenes/PDF ficticios para las pruebas (sin datos reales). |
| `test_entities.py` | Detección de entidades por regex, sin solapamientos ni modificación del texto. |
| `test_docx_export.py` | Generación de Word: formato, plantilla, tablas, numeración, saltos de página. |
| `test_project_store.py` | Guardado/recuperación de proyectos y sesiones interrumpidas. |
| `test_paths.py` | Rutas portátiles: no dependen de letra de unidad ni directorio de trabajo. |
| `test_image_prep.py` | Preprocesamiento de imagen: inclinación, recorte, páginas dobles, resolución baja. |
| `test_pdf_io.py` | Lectura de PDF (con/sin texto, protegido, dañado, multipágina) e imágenes. |
| `test_ocr_engine.py` | OCR real contra Tesseract instalado, en español, con coordenadas y confianza. |
| `test_pipeline.py` | Procesamiento completo de un expediente, cancelación, fallo parcial, uso de memoria. |
| `test_config.py` | Configuración: valores predeterminados, persistencia, recuperación ante archivo corrupto. |
| `test_logging_setup.py` | Verifica explícitamente que el registro técnico no contiene datos personales. |

## `packaging/` — empaquetado para Windows

| Archivo | Función |
|---|---|
| `TranscriptorNotarial.spec` | Especificación de PyInstaller (modo `onedir`). |
| `version_info.txt` | Metadatos de versión/fabricante incrustados en el `.exe`. |
| `build_portable.ps1` / `.bat` | Compilan y arman la carpeta `Transcriptor_Notarial_Portable` completa. |
| `verify_dependencies.py` | Verifica que estén presentes todas las dependencias antes de compilar. |
| `generate_hashes.py` | Genera el listado de archivos y hashes SHA-256 de la entrega. |
| `installer.iss` | Script de Inno Setup para el instalador opcional (no reemplaza la versión portátil). |

## `scripts/` — utilidades de desarrollo

| Archivo | Función |
|---|---|
| `generar_ejemplos.py` | Genera los documentos ficticios de `ejemplos/` y la plantilla de muestra. |
| `generar_manual_pdf.py` | Convierte `docs/MANUAL_USUARIO.md` a `docs/Manual_de_Uso.pdf`. |

## `resources/` — recursos incluidos en la carpeta portátil

| Archivo | Función |
|---|---|
| `plantillas/Plantilla_Notarial.docx` | Plantilla Word de ejemplo (encabezado, pie, márgenes). Sustituir por la real de la notaría. |
| `iconos/app.ico`, `app.png` | Ícono del ejecutable y de la aplicación. |
| `tesseract/` | **Se agrega al compilar** (no versionado): binario de Tesseract y `tessdata/spa.traineddata`. Ver `docs/INSTALACION.md`. |

## `ejemplos/` — documentos ficticios de prueba

PDF e imágenes con datos inventados (nombres, domicilios y cantidades
ficticios) para probar el programa sin exponer información real: uno con
dos páginas, uno recto y uno con inclinación deliberada.

## `docs/` y `licencias/`

| Archivo | Función |
|---|---|
| `docs/MANUAL_USUARIO.md` / `Manual_de_Uso.pdf` | Manual para el usuario final. |
| `docs/INSTALACION.md` | Cómo compilar, empaquetar, armar la USB y actualizarla. |
| `docs/DESARROLLO.md` | Cómo desarrollar y probar el proyecto. |
| `docs/LIMITACIONES.md` | Qué se validó en este entorno y qué falta validar en Windows real. |
| `docs/LEEME.txt` | Léame incluido en la raíz de la carpeta portátil. |
| `docs/ARCHIVOS.md` | Este archivo. |
| `licencias/LICENCIAS.md` | Licencias y atribuciones de todos los componentes de terceros redistribuidos. |
