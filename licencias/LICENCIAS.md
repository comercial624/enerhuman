# Licencias y atribuciones de terceros

Transcriptor Notarial es software para uso interno de la notaría que
redistribuye los siguientes componentes de código abierto. Se listan sus
licencias para cumplir con los requisitos de atribución antes de usar el
programa comercialmente.

| Componente | Licencia | Uso en este proyecto |
|---|---|---|
| [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) | Apache License 2.0 | Motor de reconocimiento de texto, incluido en `recursos/tesseract/` de la carpeta portátil. |
| [Leptonica](http://leptonica.org/) (dependencia de Tesseract) | Licencia tipo BSD | Incluida como dependencia binaria de Tesseract. |
| [PySide6 / Qt](https://www.qt.io/) | LGPL v3 (Qt for Python) | Interfaz gráfica. |
| [OpenCV](https://opencv.org/) | Apache License 2.0 | Preprocesamiento de imágenes. |
| [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/) | AGPL v3 / licencia comercial de Artifex | Lectura y rasterización de PDF. Ver nota abajo. |
| [Pillow](https://python-pillow.org/) | MIT-CMU (licencia HPND) | Manipulación de imágenes. |
| [python-docx](https://python-docx.readthedocs.io/) | MIT | Generación de archivos Word. |
| [NumPy](https://numpy.org/) | BSD 3-Clause | Cálculo numérico para el preprocesamiento de imagen. |
| [pytesseract](https://github.com/madmaze/pytesseract) | Apache License 2.0 | Interfaz de Python hacia Tesseract. |
| [pyspellchecker](https://github.com/barrust/pyspellchecker) | MIT | Corrector ortográfico local en español. |
| [pywin32](https://github.com/mhammond/pywin32) | PSF-based / licencia estilo BSD | Automatización de Word (COM) y escaneo WIA (solo Windows). |
| [PyInstaller](https://pyinstaller.org/) | GPL v2 con excepción de bootloader | Empaquetado del ejecutable; la excepción de licencia permite distribuir el `.exe` resultante sin imponer GPL a la aplicación empaquetada. |
| [Inno Setup](https://jrsoftware.org/isinfo.php) | Licencia propia de Inno Setup (gratuita, código fuente disponible) | Generación del instalador opcional. |

## Nota importante sobre PyMuPDF

PyMuPDF (el paquete `fitz`) se distribuye bajo **doble licencia**: AGPL v3
para uso de código abierto, o una licencia comercial de Artifex Software
para uso en software propietario/cerrado que no se desea publicar bajo
AGPL. **Antes de usar este programa comercialmente en la notaría, verifique
los términos vigentes de PyMuPDF/Artifex** en
https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright
y, si el uso comercial lo requiere, adquiera la licencia comercial
correspondiente o evalúe una alternativa (por ejemplo, `pypdfium2`, con
licencia BSD/Apache) para la lectura de PDF si se prefiere evitar AGPL.
Este proyecto no incluye ninguna licencia comercial de PyMuPDF: es
responsabilidad de quien lo distribuya comercialmente resolver este punto.

## Cómo se distribuyen estos avisos en la carpeta portátil

La carpeta `licencias/` completa (este archivo más los textos de licencia
individuales, cuando el proyecto de origen los distribuye como archivo de
texto independiente) se copia dentro de
`Transcriptor_Notarial_Portable\licencias\` al generar la versión
portátil, junto con el código fuente completo de este repositorio (los
componentes con licencia copyleft de biblioteca, como LGPL, permiten el
enlace dinámico sin obligar a liberar el código propio de la aplicación,
siempre que el usuario final pueda, si lo solicita, sustituir la biblioteca
LGPL por una versión propia — ver texto completo de la LGPL v3 más abajo
para el caso de Qt/PySide6).

## Textos de licencia

Los textos completos de cada licencia mencionada arriba están disponibles
públicamente en los enlaces de la tabla. Antes de la distribución final a
la notaría, copie aquí (`licencias/`) el texto completo de cada licencia
tal como lo exija cada proyecto (algunas, como Apache 2.0 y MIT, solo
requieren conservar el aviso de copyright; LGPL y AGPL tienen requisitos
adicionales que debe revisar si planea modificar esas bibliotecas).
