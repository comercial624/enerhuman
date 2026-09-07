"""Hilos de trabajo en segundo plano para no congelar la interfaz.

El procesamiento OCR de un expediente completo puede tardar varios minutos;
se ejecuta en un QThread independiente que reporta progreso mediante
señales y puede cancelarse de forma segura entre páginas.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from ..core import pipeline
from ..core.pdf_io import PaginaFuente
from ..core.project_store import Proyecto, AlmacenProyectos


class HiloProcesamiento(QThread):
    progreso = Signal(object)  # pipeline.ProgresoPagina
    finalizado = Signal(object)  # Proyecto
    error_fatal = Signal(str)

    def __init__(
        self,
        paginas_fuente: list[PaginaFuente],
        idioma_ocr: str,
        carpeta_temporal: Path,
        proyecto: Proyecto,
        almacen: AlmacenProyectos,
        parent=None,
    ):
        super().__init__(parent)
        self._paginas_fuente = paginas_fuente
        self._idioma_ocr = idioma_ocr
        self._carpeta_temporal = carpeta_temporal
        self._proyecto = proyecto
        self._almacen = almacen
        self._cancelar = False

    def solicitar_cancelacion(self) -> None:
        self._cancelar = True

    def _debe_cancelar(self) -> bool:
        return self._cancelar

    def run(self) -> None:
        try:
            proyecto = pipeline.procesar_expediente(
                self._paginas_fuente,
                self._idioma_ocr,
                self._carpeta_temporal,
                self._proyecto,
                self._almacen,
                callback_progreso=self.progreso.emit,
                debe_cancelar=self._debe_cancelar,
            )
            self.finalizado.emit(proyecto)
        except Exception as e:  # salvaguarda: nunca debe tumbar la GUI
            self.error_fatal.emit(f"{type(e).__name__}: {e}")
