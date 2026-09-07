"""Editor de la transcripción (panel derecho de la vista de revisión).

Resalta en amarillo las palabras con baja confianza del OCR y, con un color
distinto, los elementos detectados por `core.entities` (nombres, fechas,
cantidades, domicilios, etc.). Al hacer clic sobre una palabra dudosa se
emite una señal con su ubicación aproximada en la imagen original.

Deshacer/rehacer se apoya en el soporte nativo de QTextEdit (Ctrl+Z /
Ctrl+Shift+Z), que ya mantiene una pila de cambios de edición de texto.
"""
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (
    QSyntaxHighlighter, QTextCharFormat, QColor, QTextCursor, QTextDocument
)
from PySide6.QtWidgets import QTextEdit

from ...core import entities

COLOR_BAJA_CONFIANZA = QColor(255, 235, 59)  # amarillo
COLOR_BAJA_CONFIANZA_REVISADA = QColor(197, 225, 165)  # verde suave
COLOR_ENTIDAD = QColor(179, 229, 252)  # celeste


@dataclass
class PalabraIndexada:
    texto: str
    confianza: float
    x: int
    y: int
    ancho: int
    alto: int
    revisada: bool = False


def _normalizar(palabra: str) -> str:
    return "".join(c for c in palabra.lower() if c.isalnum())


class ResaltadorTranscripcion(QSyntaxHighlighter):
    def __init__(self, documento: QTextDocument, editor: "EditorTranscripcion"):
        super().__init__(documento)
        self._editor = editor
        self.mostrar_entidades = True
        self.mostrar_baja_confianza = True

    def highlightBlock(self, texto: str) -> None:
        if self.mostrar_baja_confianza:
            for palabra in self._editor.palabras_baja_confianza():
                clave = _normalizar(palabra.texto)
                if not clave:
                    continue
                inicio = 0
                while True:
                    pos = texto.lower().find(palabra.texto.lower(), inicio)
                    if pos == -1:
                        break
                    formato = QTextCharFormat()
                    formato.setBackground(
                        COLOR_BAJA_CONFIANZA_REVISADA if palabra.revisada else COLOR_BAJA_CONFIANZA
                    )
                    self.setFormat(pos, len(palabra.texto), formato)
                    inicio = pos + len(palabra.texto)

        if self.mostrar_entidades:
            for coincidencia in entities.detectar_entidades(texto):
                formato = QTextCharFormat()
                formato.setUnderlineColor(COLOR_ENTIDAD.darker(150))
                formato.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SingleUnderline)
                formato.setToolTip(coincidencia.tipo.value)
                self.setFormat(coincidencia.inicio, coincidencia.fin - coincidencia.inicio, formato)


class EditorTranscripcion(QTextEdit):
    palabra_dudosa_seleccionada = Signal(int, int, int, int)  # x, y, ancho, alto

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(False)
        self._palabras: list[PalabraIndexada] = []
        self._resaltador = ResaltadorTranscripcion(self.document(), self)
        self.cursorPositionChanged.connect(self._al_mover_cursor)

    def cargar_texto(self, texto: str, palabras: list[PalabraIndexada]) -> None:
        self._palabras = palabras
        self.blockSignals(True)
        self.setPlainText(texto)
        self.blockSignals(False)
        self.document().clearUndoRedoStacks()
        self._resaltador.rehighlight()

    def palabras_baja_confianza(self) -> list[PalabraIndexada]:
        return self._palabras

    def establecer_umbral_y_lista(self, palabras: list[PalabraIndexada]) -> None:
        self._palabras = palabras
        self._resaltador.rehighlight()

    def _palabra_bajo_cursor(self) -> str:
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        return cursor.selectedText()

    def _al_mover_cursor(self) -> None:
        palabra_texto = self._palabra_bajo_cursor()
        if not palabra_texto:
            return
        clave = _normalizar(palabra_texto)
        for palabra in self._palabras:
            if _normalizar(palabra.texto) == clave:
                self.palabra_dudosa_seleccionada.emit(palabra.x, palabra.y, palabra.ancho, palabra.alto)
                return

    def marcar_palabra_actual_como_revisada(self) -> bool:
        palabra_texto = self._palabra_bajo_cursor()
        clave = _normalizar(palabra_texto)
        if not clave:
            return False
        encontrada = False
        for palabra in self._palabras:
            if _normalizar(palabra.texto) == clave:
                palabra.revisada = True
                encontrada = True
        if encontrada:
            self._resaltador.rehighlight()
        return encontrada

    def buscar_siguiente(self, texto_buscado: str, mayusculas_exacto: bool = False) -> bool:
        opciones = QTextDocument.FindFlag(0)
        if mayusculas_exacto:
            opciones |= QTextDocument.FindFlag.FindCaseSensitively
        encontrado = self.find(texto_buscado, opciones)
        if not encontrado:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self.setTextCursor(cursor)
            encontrado = self.find(texto_buscado, opciones)
        return encontrado

    def reemplazar_todo(self, buscar: str, reemplazar: str, mayusculas_exacto: bool = False) -> int:
        if not buscar:
            return 0
        texto_actual = self.toPlainText()
        if mayusculas_exacto:
            ocurrencias = texto_actual.count(buscar)
            nuevo_texto = texto_actual.replace(buscar, reemplazar)
        else:
            import re
            patron = re.compile(re.escape(buscar), re.IGNORECASE)
            ocurrencias = len(patron.findall(texto_actual))
            nuevo_texto = patron.sub(reemplazar, texto_actual)
        if ocurrencias:
            cursor = self.textCursor()
            cursor.select(QTextCursor.SelectionType.Document)
            cursor.insertText(nuevo_texto)
        return ocurrencias
