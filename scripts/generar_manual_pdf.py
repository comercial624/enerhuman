#!/usr/bin/env python3
"""Convierte docs/MANUAL_USUARIO.md a docs/Manual_de_Uso.pdf usando
reportlab (sin depender de herramientas externas de conversión).

Es un conversor deliberadamente simple: soporta encabezados (#, ##),
listas con "-" y tablas markdown básicas. Suficiente para un manual breve;
no pretende ser un motor de Markdown completo.

Uso:
    python scripts/generar_manual_pdf.py
"""
from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, Table, TableStyle,
)

RAIZ = Path(__file__).resolve().parent.parent
ORIGEN = RAIZ / "docs" / "MANUAL_USUARIO.md"
DESTINO = RAIZ / "docs" / "Manual_de_Uso.pdf"


def _escapar(texto: str) -> str:
    texto = texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    texto = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", texto)
    texto = re.sub(r"`(.+?)`", r"<font face='Courier'>\1</font>", texto)
    return texto


def convertir(ruta_md: Path, ruta_pdf: Path) -> None:
    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle("TituloManual", parent=estilos["Title"], fontSize=20, spaceAfter=16)
    estilo_h2 = ParagraphStyle("H2", parent=estilos["Heading2"], spaceBefore=14, spaceAfter=8)
    estilo_normal = ParagraphStyle("NormalEs", parent=estilos["Normal"], fontSize=10.5, leading=14)

    elementos = []
    lineas = ruta_md.read_text(encoding="utf-8").splitlines()

    i = 0
    while i < len(lineas):
        linea = lineas[i].rstrip()

        if linea.startswith("# "):
            elementos.append(Paragraph(_escapar(linea[2:]), estilo_titulo))
        elif linea.startswith("## "):
            elementos.append(Paragraph(_escapar(linea[3:]), estilo_h2))
        elif linea.startswith("|"):
            filas = []
            while i < len(lineas) and lineas[i].strip().startswith("|"):
                celdas = [c.strip() for c in lineas[i].strip().strip("|").split("|")]
                if not set(celdas[0]) <= {"-", " "}:
                    filas.append(celdas)
                i += 1
            i -= 1
            if filas:
                tabla = Table(filas, hAlign="LEFT")
                tabla.setStyle(TableStyle([
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]))
                elementos.append(tabla)
                elementos.append(Spacer(1, 10))
        elif linea.startswith("- "):
            items = []
            while i < len(lineas) and lineas[i].strip().startswith("- "):
                items.append(ListItem(Paragraph(_escapar(lineas[i].strip()[2:]), estilo_normal)))
                i += 1
            i -= 1
            elementos.append(ListFlowable(items, bulletType="bullet", leftIndent=14))
        elif re.match(r"^\d+\. ", linea):
            items = []
            while i < len(lineas) and re.match(r"^\d+\. ", lineas[i].strip()):
                texto = re.sub(r"^\d+\.\s*", "", lineas[i].strip())
                items.append(ListItem(Paragraph(_escapar(texto), estilo_normal)))
                i += 1
            i -= 1
            elementos.append(ListFlowable(items, bulletType="1", leftIndent=14))
        elif linea.strip() == "":
            elementos.append(Spacer(1, 6))
        else:
            elementos.append(Paragraph(_escapar(linea), estilo_normal))

        i += 1

    documento = SimpleDocTemplate(
        str(ruta_pdf), pagesize=LETTER,
        topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=2.5 * cm, rightMargin=2 * cm,
        title="Manual de Uso - Transcriptor Notarial",
    )
    documento.build(elementos)


if __name__ == "__main__":
    convertir(ORIGEN, DESTINO)
    print(f"Manual generado en: {DESTINO}")
