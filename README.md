# Transcriptor Notarial

Aplicación de escritorio para Windows que convierte actas y documentos
notariales escaneados en borradores de Word editables, mediante OCR
**100% local**: sin nube, sin APIs externas, sin telemetría, sin cuentas de
usuario.

## Qué hace

1. Lee PDF (escaneado o con texto), JPG, PNG o TIFF, o escanea directo (WIA).
2. Prepara la imagen (endereza, quita sombras, mejora contraste) sin destruir
   el original.
3. Reconoce el texto con Tesseract OCR en español.
4. Muestra imagen y texto lado a lado para revisión, resaltando en amarillo
   las palabras de baja confianza y marcando nombres, fechas, cantidades,
   domicilios, folios, etc. (sin corregir nada automáticamente).
5. Genera un `.docx` editable — limpio o respetando una plantilla de la
   notaría — y lo abre en Microsoft Word.

## Estado de este entregable — léase primero

Este repositorio se desarrolló en un entorno **Linux sin Windows, sin Word
y sin escáner físico**. Por eso:

| Componente | Estado |
|---|---|
| Código fuente completo (GUI, OCR, exportación, WIA, COM) | ✅ Terminado |
| Pruebas de lógica pura (regex, Word, proyectos, imagen) | ✅ 62 pruebas, todas en verde |
| Prueba end-to-end con Tesseract real (español) | ✅ Verificada en este entorno |
| Prueba de la GUI (construcción de la ventana, headless) | ✅ Verificada |
| Compilación del `.exe` de Windows | ❌ Requiere Windows (PyInstaller no cruza de SO) |
| Pruebas en VM limpia de Windows 10/11 | ❌ Requiere Windows |
| Apertura real en Microsoft Word / escaneo WIA real | ❌ Requiere Windows + Word + escáner |

Ver [`docs/LIMITACIONES.md`](docs/LIMITACIONES.md) para el detalle completo
y qué hacer para terminar la validación en una PC Windows real.

## Inicio rápido (desarrollo, cualquier SO con Python 3.11+)

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pytest tests/ -q                   # 62 pruebas
python run_dev.py                  # abre la GUI (requiere entorno gráfico)
```

En Windows, `run_dev.bat` hace lo mismo con doble clic (una vez creado el
entorno virtual).

## Generar la versión portátil para USB (solo desde Windows)

```powershell
powershell -ExecutionPolicy Bypass -File packaging\build_portable.ps1
```

Ver [`docs/INSTALACION.md`](docs/INSTALACION.md) para los requisitos
previos (Tesseract para Windows, etc.) y el detalle paso a paso.

## Estructura del proyecto

```
transcriptor_notarial/       Código fuente de la aplicación
  app.py                     Punto de entrada
  config.py                  Configuración persistente
  paths.py                   Resolución de rutas portátiles (sin letra de unidad fija)
  logging_setup.py           Registro técnico sin datos personales
  core/                      Lógica de negocio (sin dependencias de GUI)
    pdf_io.py                 Lectura/unión de PDF e imágenes
    image_prep.py             Preprocesamiento de imagen (OpenCV)
    ocr_engine.py              Reconocimiento OCR (Tesseract)
    entities.py                Detección de nombres, fechas, cantidades, etc.
    docx_export.py             Generación del Word final
    project_store.py           Guardado/recuperación de sesión
    pipeline.py                 Orquestación del procesamiento por página
    word_integration.py        Apertura en Word (COM, solo Windows)
    scanner_wia.py              Escaneo directo (WIA, solo Windows)
    spellcheck.py               Corrector ortográfico local
  gui/                        Interfaz PySide6
    main_window.py             Ventana principal (los 10 botones)
    review_view.py              Vista de revisión (imagen + texto)
    workers.py                  Hilos en segundo plano
    config_dialog.py            Configuración
    widgets/                    Visor de imagen y editor de texto
tests/                        Pruebas automatizadas (pytest)
resources/                    Plantilla Word, iconos (Tesseract se agrega al compilar)
packaging/                    Spec de PyInstaller, scripts de build, Inno Setup
scripts/                      Utilidades de desarrollo (generar ejemplos, etc.)
ejemplos/                     Documentos ficticios de prueba (sin datos reales)
docs/                         Manual de usuario, instalación, desarrollo, limitaciones
licencias/                    Licencias y atribuciones de terceros
```

## Documentación

- [`docs/MANUAL_USUARIO.md`](docs/MANUAL_USUARIO.md) — cómo usar el programa (para el empleado).
- [`docs/INSTALACION.md`](docs/INSTALACION.md) — cómo compilar, armar la USB y actualizarla.
- [`docs/DESARROLLO.md`](docs/DESARROLLO.md) — cómo desarrollar, probar y depurar.
- [`docs/LIMITACIONES.md`](docs/LIMITACIONES.md) — qué falta validar y por qué.
- [`licencias/LICENCIAS.md`](licencias/LICENCIAS.md) — licencias de todo lo redistribuido.

## Privacidad y seguridad (resumen)

- Todo el procesamiento ocurre en la computadora local; no hay llamadas de red.
- No se guardan documentos ni contenido reconocido en el registro técnico
  (solo fecha/hora, operación, duración y número de páginas).
- Los archivos originales nunca se modifican; se trabaja sobre copias temporales.
- Sin cuentas de usuario, sin telemetría, sin actualizaciones automáticas.
