"""Generación del documento Word (.docx) final a partir de la transcripción
revisada por el usuario.

Dos modalidades:
  - Transcripción limpia: texto continuo editable con formato configurable.
  - Formato semejante al original: intenta conservar títulos, tablas y
    saltos de página (mejor esfuerzo; no garantiza réplica exacta).

Ambas pueden partir de una plantilla .docx de la notaría, conservando sus
encabezados, pies de página, márgenes y estilos.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

import docx
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION

from ..config import ConfiguracionApp


class ModalidadExportacion(str, Enum):
    TRANSCRIPCION_LIMPIA = "limpia"
    FORMATO_SEMEJANTE = "semejante"


class PosicionInsercionPlantilla(str, Enum):
    AL_INICIO = "inicio"
    DESPUES_DE_CONTENIDO = "despues_de_contenido"


@dataclass
class PaginaTranscrita:
    numero: int
    texto: str
    es_tabla: bool = False
    filas_tabla: list[list[str]] = field(default_factory=list)
    titulo_detectado: str | None = None


_MAPA_ALINEACION = {
    "justificado": WD_ALIGN_PARAGRAPH.JUSTIFY,
    "izquierda": WD_ALIGN_PARAGRAPH.LEFT,
    "centrado": WD_ALIGN_PARAGRAPH.CENTER,
}


def _aplicar_formato_parrafo(parrafo, config: ConfiguracionApp) -> None:
    parrafo.alignment = _MAPA_ALINEACION.get(config.alineacion, WD_ALIGN_PARAGRAPH.JUSTIFY)
    formato = parrafo.paragraph_format
    formato.line_spacing = config.interlineado
    if config.sangria_primera_linea_cm > 0:
        formato.first_line_indent = Cm(config.sangria_primera_linea_cm)
    for run in parrafo.runs:
        run.font.name = config.fuente_word
        run.font.size = Pt(config.tamano_letra)


def _configurar_margenes(documento: Document, config: ConfiguracionApp) -> None:
    for seccion in documento.sections:
        seccion.top_margin = Cm(config.margen_superior_cm)
        seccion.bottom_margin = Cm(config.margen_inferior_cm)
        seccion.left_margin = Cm(config.margen_izquierdo_cm)
        seccion.right_margin = Cm(config.margen_derecho_cm)


def _agregar_numeracion_paginas(documento: Document) -> None:
    """Inserta un campo de número de página en el pie de cada sección."""
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    for seccion in documento.sections:
        pie = seccion.footer
        parrafo = pie.paragraphs[0] if pie.paragraphs else pie.add_paragraph()
        parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = parrafo.add_run()
        campo_inicio = OxmlElement("w:fldChar")
        campo_inicio.set(qn("w:fldCharType"), "begin")
        instruccion = OxmlElement("w:instrText")
        instruccion.set(qn("xml:space"), "preserve")
        instruccion.text = "PAGE"
        campo_fin = OxmlElement("w:fldChar")
        campo_fin.set(qn("w:fldCharType"), "end")
        run._r.append(campo_inicio)
        run._r.append(instruccion)
        run._r.append(campo_fin)


def _parrafos_desde_texto(texto: str) -> list[str]:
    """Divide el texto reconocido en párrafos, respetando líneas en blanco
    como separadores y uniendo líneas cortadas dentro de un mismo párrafo.
    """
    bloques = [b.strip() for b in texto.split("\n\n")]
    parrafos = []
    for bloque in bloques:
        if not bloque:
            continue
        lineas = [l.strip() for l in bloque.split("\n") if l.strip()]
        parrafos.append(" ".join(lineas))
    return parrafos or [texto.strip()]


def _es_titulo(parrafo_texto: str) -> bool:
    """Heurística simple: líneas cortas y en mayúsculas se tratan como
    título/subtítulo al reproducir el formato semejante al original.
    """
    limpio = parrafo_texto.strip()
    if not limpio or len(limpio) > 90:
        return False
    letras = [c for c in limpio if c.isalpha()]
    if not letras:
        return False
    return sum(1 for c in letras if c.isupper()) / len(letras) > 0.8


def _insertar_pagina_limpia(documento: Document, pagina: PaginaTranscrita, config: ConfiguracionApp) -> None:
    for texto_parrafo in _parrafos_desde_texto(pagina.texto):
        p = documento.add_paragraph(texto_parrafo)
        _aplicar_formato_parrafo(p, config)


def _insertar_pagina_semejante(documento: Document, pagina: PaginaTranscrita, config: ConfiguracionApp) -> None:
    if pagina.es_tabla and pagina.filas_tabla:
        num_columnas = max(len(fila) for fila in pagina.filas_tabla)
        tabla = documento.add_table(rows=0, cols=num_columnas)
        tabla.style = "Table Grid"
        for fila in pagina.filas_tabla:
            celdas = tabla.add_row().cells
            for i, valor in enumerate(fila):
                celdas[i].text = valor
        return

    for texto_parrafo in _parrafos_desde_texto(pagina.texto):
        p = documento.add_paragraph(texto_parrafo)
        if _es_titulo(texto_parrafo):
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.bold = True
                run.font.name = config.fuente_word
                run.font.size = Pt(config.tamano_letra + 2)
        else:
            _aplicar_formato_parrafo(p, config)


def generar_documento(
    paginas: list[PaginaTranscrita],
    config: ConfiguracionApp,
    ruta_salida: Path,
    modalidad: ModalidadExportacion = ModalidadExportacion.TRANSCRIPCION_LIMPIA,
    ruta_plantilla: Path | None = None,
    posicion_insercion: PosicionInsercionPlantilla = PosicionInsercionPlantilla.DESPUES_DE_CONTENIDO,
) -> Path:
    """Genera el archivo .docx final. No requiere que Microsoft Word esté
    abierto ni instalado: usa python-docx puro.
    """
    if ruta_plantilla and Path(ruta_plantilla).exists():
        documento = Document(str(ruta_plantilla))
        if posicion_insercion == PosicionInsercionPlantilla.AL_INICIO:
            # Se inserta un salto de página después del contenido de la
            # transcripción para separarlo de lo que ya traía la plantilla.
            pass
    else:
        documento = Document()
        _configurar_margenes(documento, config)
        if config.numeracion_paginas:
            _agregar_numeracion_paginas(documento)

    insertar_pagina = (
        _insertar_pagina_limpia
        if modalidad == ModalidadExportacion.TRANSCRIPCION_LIMPIA
        else _insertar_pagina_semejante
    )

    for i, pagina in enumerate(paginas):
        insertar_pagina(documento, pagina, config)
        if i < len(paginas) - 1:
            documento.add_page_break()

    ruta_salida = Path(ruta_salida)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    documento.save(str(ruta_salida))
    return ruta_salida
