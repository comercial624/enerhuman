# Limitaciones conocidas

## 1. No compilado ni probado en Windows real (limitación del entorno de desarrollo)

Este proyecto se generó en un contenedor Linux sin Windows, sin Microsoft
Word, sin escáner físico y sin acceso a una VM de Windows. Esto es una
limitación **del entorno en que se desarrolló**, no del diseño del
programa. Concretamente, **falta hacer en una PC Windows real**:

- Compilar `TranscriptorNotarial.exe` con PyInstaller (`packaging/build_portable.ps1`).
  PyInstaller empaqueta para el sistema operativo anfitrión: no puede
  generarse un `.exe` de Windows desde Linux.
- Incluir una copia legal de Tesseract OCR para Windows en
  `recursos/tesseract/` (ver `docs/INSTALACION.md`, sección 2).
- Probar en una VM limpia de Windows 10 y otra de Windows 11 sin Python,
  Tesseract, OpenCV ni herramientas de desarrollo instaladas (las 14
  pruebas de portabilidad que pide el encargo original: ejecución desde
  USB con distintas letras de unidad, rutas con espacios y acentos, sin
  permisos de administrador, retiro inesperado de la USB, con Windows
  Defender activo, etc.).
- Probar la apertura real en Microsoft Word (COM vía `pywin32`), con Word
  cerrado y con Word ya abierto con otros documentos.
- Probar el escaneo directo WIA con un escáner físico y su controlador.
- Compilar el instalador opcional con Inno Setup 6.
- Firmar digitalmente el ejecutable (el proyecto está preparado para ello —
  metadatos de versión y fabricante correctos en `packaging/version_info.txt`
  — pero la firma en sí requiere un certificado de firma de código que
  está fuera del alcance de este entregable).

## 2. Lo que sí se validó en este entorno

- **62 pruebas automatizadas en verde** (`pytest tests/ -q`), incluyendo:
  - Detección de entidades por regex (nombres, fechas, cantidades, folios,
    domicilios, códigos postales, correos, etc.), sin solapamientos y sin
    modificar el texto original.
  - Generación de documentos Word (`.docx`): formato, fuente, márgenes,
    tablas, plantillas, numeración de páginas, saltos de página.
  - Persistencia y recuperación de proyectos/sesión.
  - Resolución de rutas sin depender de letra de unidad ni directorio de
    trabajo (simulando ejecución desde una "USB" en Linux).
  - Preprocesamiento de imagen (inclinación, recorte, separación de
    páginas dobles) sin destruir el contenido.
  - Lectura de PDF (con y sin capa de texto, protegido, dañado, multipágina).
  - **OCR real contra Tesseract 5.3 instalado en el entorno de pruebas**,
    con el paquete de idioma español, incluyendo reconocimiento de texto,
    coordenadas, confianza por palabra y verificación de que el idioma
    solicitado exista.
  - Pipeline completo de principio a fin: varias páginas, cancelación a
    mitad de proceso, continuar tras el fallo de una página, guardado
    incremental, no cargar todas las imágenes en memoria a la vez.
  - Registro técnico: se comprobó explícitamente que el log **no** contiene
    texto de prueba con datos personales, solo los campos permitidos.
- **Demostración end-to-end real**: se procesó un PDF de ejemplo (ficticio)
  de dos páginas con el pipeline completo — OCR en español, detección de
  baja confianza, exportación a `.docx` usando la plantilla de ejemplo —
  de punta a punta, sin intervención manual.
- **Construcción de la ventana principal de PySide6** en modo headless
  (`QT_QPA_PLATFORM=offscreen`): confirma que la GUI se construye sin
  errores de sintaxis ni de referencias entre widgets, aunque no reemplaza
  una prueba visual interactiva en Windows.

## 3. Limitaciones de diseño (independientes del entorno)

- **La separación de páginas dobles** usa una heurística simple (columna
  central casi totalmente oscura). Documentos con una encuadernación poco
  contrastada, o con texto muy denso exactamente en el centro, pueden dar
  falsos negativos o positivos ocasionales; por diseño nunca se aplica de
  forma irreversible sin que el usuario pueda revisar el resultado.
- **La corrección de inclinación** (Hough) funciona bien para inclinaciones
  moderadas (unos pocos grados, típico de un escaneo manual); documentos
  girados 90°/180°/270° deben corregirse con el botón "Girar" manual en la
  vista de revisión, no se auto-detectan como rotación completa.
- **El "formato semejante al original"** es de mejor esfuerzo: reproduce
  títulos (por heurística de mayúsculas/longitud de línea) y tablas
  explícitas, pero no garantiza una réplica exacta del diseño original en
  documentos con maquetación compleja (columnas múltiples, texto
  superpuesto a gráficos, etc.), tal como se advierte en la propia
  interfaz.
- **El corrector ortográfico** (`pyspellchecker`) es una ayuda visual, no
  una verdad absoluta: términos jurídicos y nombres propios legítimos
  aparecerán como "desconocidos" con frecuencia; el usuario decide.
- **La detección de nombres completos** por regex (mayúsculas iniciales)
  puede generar falsos positivos/negativos con nombres compuestos poco
  usuales o con el ruido típico de un OCR imperfecto; es una ayuda de
  revisión, no una fuente de verdad.
- **WIA** depende enteramente del controlador del escáner instalado en la
  computadora del cliente; no todos los escáneres exponen las mismas
  propiedades de resolución/color, por lo que en algunos modelos el
  programa usará los valores predeterminados del dispositivo en lugar de
  los configurados.

## 4. Qué falta para considerar el proyecto "terminado" según el encargo original

Siguiendo los criterios de aceptación del encargo, falta específicamente:

1. Compilar el `.exe` y armar la carpeta portátil real (pasos 1-2 de
   `docs/INSTALACION.md`).
2. Ejecutar las 14 pruebas de portabilidad en VMs limpias de Windows
   10/11 listadas en `docs/INSTALACION.md`, sección 11.
3. Generar el ZIP final, calcular sus hashes SHA-256
   (`packaging/generate_hashes.py` ya está listo para esto) y producir el
   informe de pruebas correspondiente.
4. Firmar digitalmente el ejecutable si la notaría cuenta con un
   certificado de firma de código (opcional, pero recomendado a futuro).

Todo el código y los scripts necesarios para completar estos pasos están
en este repositorio; requieren únicamente ejecutarse en Windows.
