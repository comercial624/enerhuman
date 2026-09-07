"""Visor de imagen para el panel izquierdo de la vista de revisión.

Permite acercar/alejar, desplazar, girar y resaltar la ubicación aproximada
de una palabra dudosa seleccionada en el texto.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QTransform
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem


class VisorImagen(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._escena = QGraphicsScene(self)
        self.setScene(self._escena)
        self._item_pixmap: QGraphicsPixmapItem | None = None
        self._item_resaltado: QGraphicsRectItem | None = None
        self._rotacion_grados = 0
        self._factor_zoom = 1.0

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

    def cargar_imagen(self, ruta: str) -> None:
        pixmap = QPixmap(ruta)
        self._escena.clear()
        self._item_pixmap = self._escena.addPixmap(pixmap)
        self._item_resaltado = None
        self._escena.setSceneRect(QRectF(pixmap.rect()))
        self._rotacion_grados = 0
        self.resetTransform()
        self._factor_zoom = 1.0
        self.ajustar_a_ventana()

    def ajustar_a_ventana(self) -> None:
        if self._item_pixmap is not None:
            self.fitInView(self._item_pixmap, Qt.AspectRatioMode.KeepAspectRatio)

    def acercar(self) -> None:
        self._factor_zoom *= 1.25
        self.scale(1.25, 1.25)

    def alejar(self) -> None:
        self._factor_zoom /= 1.25
        self.scale(0.8, 0.8)

    def girar(self, grados: int) -> None:
        self._rotacion_grados = (self._rotacion_grados + grados) % 360
        self.setTransform(QTransform().rotate(self._rotacion_grados))
        self.ajustar_a_ventana()

    @property
    def rotacion_actual(self) -> int:
        return self._rotacion_grados

    def resaltar_zona(self, x: int, y: int, ancho: int, alto: int) -> None:
        """Dibuja/actualiza un rectángulo resaltando la ubicación aproximada
        de una palabra dudosa, seleccionada desde el panel de texto.
        """
        if self._item_resaltado is not None:
            self._escena.removeItem(self._item_resaltado)
        pluma = QPen(QColor(255, 165, 0), 3)
        self._item_resaltado = self._escena.addRect(x, y, ancho, alto, pluma)
        self.centerOn(x + ancho / 2, y + alto / 2)

    def limpiar_resaltado(self) -> None:
        if self._item_resaltado is not None:
            self._escena.removeItem(self._item_resaltado)
            self._item_resaltado = None

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.acercar()
        else:
            self.alejar()
