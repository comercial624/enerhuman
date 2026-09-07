# Manual de uso — Transcriptor Notarial

Guía breve para usar el programa sin conocimientos técnicos.

## 1. Abrir el programa

- **Desde la memoria USB:** abra la carpeta `Transcriptor_Notarial_Portable`
  y haga doble clic en `TranscriptorNotarial.exe`. No importa si la USB
  aparece como `D:`, `E:` u otra letra: el programa funciona igual.
- **Si lo copió a la computadora** (ver sección 8), use el acceso directo
  del escritorio o del menú Inicio.

No necesita instalar nada más. No necesita Internet.

**No retire la memoria USB mientras el programa esté abierto ni mientras
esté procesando un documento.**

## 2. Agregar el documento

Tiene tres formas de empezar:

- **Escanear documento:** si hay un escáner instalado y detectado, escanea
  una página directamente.
- **Seleccionar PDF o imágenes:** elija uno o varios archivos PDF, JPG, PNG
  o TIFF ya existentes.
- **Agregar páginas:** suma más archivos a lo ya seleccionado.

Las páginas aparecen listadas en el orden en que se agregaron. Use
**Ordenar páginas** (arrastrando en la lista) si necesita cambiar el orden
antes de procesar — por ejemplo, si escaneó las hojas fuera de orden.

## 3. Procesar el documento

Presione **Procesar documento**. El programa le pedirá un nombre para
identificar el expediente y luego mostrará una barra de progreso con:

- Página que se está procesando y total de páginas.
- Porcentaje aproximado.
- Estado: preparando imagen, reconociendo texto, creando Word o finalizado.
- Tiempo restante estimado.

Si necesita detenerlo, use **Cancelar procesamiento**: se detiene después
de terminar la página en curso, sin perder lo ya procesado.

Si una página en particular falla, el programa continúa con las demás y
la marca para que la revise por separado.

## 4. Revisar la transcripción

Presione **Revisar transcripción**. Verá dos paneles:

- **Izquierda:** la imagen original de la página. Puede acercar, alejar,
  girar y desplazarse con el mouse. Use los botones de página
  anterior/siguiente para moverse por el expediente.
- **Derecha:** el texto reconocido, editable directamente.

Las palabras resaltadas en **amarillo** son las que el OCR reconoció con
baja confianza: revíselas con cuidado contra la imagen. Al hacer clic sobre
una de ellas, la imagen de la izquierda salta a su ubicación aproximada.

Los textos subrayados en celeste son elementos que el programa identificó
automáticamente como relevantes (nombres, fechas, cantidades, domicilios,
folios, claves catastrales, correos, etc.) para que los revise con
atención — **el programa no los corrige por usted**.

Si el texto trae una cantidad en número y otra en letra, aparecerá una
advertencia debajo del texto pidiéndole que compruebe que ambas coincidan.

Herramientas disponibles en el panel derecho:

- **Deshacer / Rehacer** — para corregir errores de edición propios.
- **Buscar y reemplazar** — para cambios repetidos en todo el texto.
- **Marcar palabra como revisada** — coloque el cursor sobre una palabra
  resaltada en amarillo y presione este botón; cambia a verde para indicar
  que ya la revisó.
- **Insertar leyenda** — para firmas, sellos, rúbricas, huellas o texto
  ilegible que el OCR no puede transcribir. El programa nunca inserta estas
  leyendas automáticamente; usted decide dónde y cuándo agregarlas.

## 5. Guardar en Word

Presione **Guardar en Word**. Elija la carpeta de destino (por defecto,
`Documentos\Transcripciones Notariales`) y el nombre del archivo. El
programa genera un `.docx` completamente editable.

Si configuró una plantilla de la notaría (ver Configuración), el documento
conservará su encabezado, pie de página, márgenes y estilos.

## 6. Abrir en Word

Presione **Abrir en Word** para abrir el documento recién generado en
Microsoft Word y continuar editándolo ahí si lo necesita. Si Word ya está
abierto con otros documentos, no se cierran: el nuevo documento se abre
junto a ellos.

## 7. Abrir carpeta de destino

Abre, en el explorador de Windows, la carpeta donde se están guardando los
documentos generados.

## 8. Copiar el programa a esta computadora (opcional)

Si prefiere no depender de la memoria USB, use el menú
**Archivo → Copiar programa a esta computadora**. Esto copia el programa a
una carpeta local (no requiere permisos de administrador) y puede crear
accesos directos en el escritorio y el menú Inicio. El programa también
sigue funcionando directamente desde la USB si lo prefiere así.

## 9. Configuración

En el menú **Archivo → Configuración** puede ajustar: carpetas de entrada y
salida, resolución y modo de color del escáner, idioma del OCR, umbral de
baja confianza, fuente y tamaño de letra del Word, márgenes, interlineado,
plantilla predeterminada, y si se abre Word automáticamente al terminar.

También puede **borrar el historial técnico** desde ahí (ver sección de
privacidad más abajo).

## 10. Recuperar una sesión interrumpida

Si el programa se cerró de forma inesperada (corte de luz, se retiró la
USB, etc.), al volver a abrirlo le preguntará si desea recuperar el
expediente que quedó a medio procesar.

## Privacidad

- El programa nunca envía el documento ni su contenido a Internet.
- El historial técnico solo guarda fecha, operación, duración y número de
  páginas — nunca el texto de las actas ni datos personales.
- Los archivos originales nunca se modifican.

## Problemas comunes

| Situación | Qué hacer |
|---|---|
| "No se encontró Tesseract OCR" | Verifique que la carpeta `recursos\tesseract` esté completa junto al programa. No la mueva ni renombre. |
| "No se detectó ningún escáner" | Use "Seleccionar PDF o imágenes" en su lugar; verifique que el escáner esté encendido y con el controlador instalado. |
| El PDF pide contraseña | El programa no puede leer PDF protegidos; quite la protección con su lector de PDF antes de procesarlo. |
| Word no abre automáticamente | Verifique que Microsoft Word esté instalado; puede abrir el archivo manualmente desde la carpeta de destino. |
| Windows muestra una advertencia al abrir el programa | Es normal en programas nuevos sin firma digital (SmartScreen). Elija "Más información" → "Ejecutar de todas formas". No es un virus. |
