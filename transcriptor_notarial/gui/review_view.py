"""Vista de revisión: panel izquierdo (imagen) + panel derecho (texto)."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QPushButton, QLabel,
    QToolBar, QLineEdit, QDialog, QFormLayout, QDialogButtonBox, QMenu,
    QMessageBox,
)

from ..core.project_store import Proyecto, PaginaProyecto
from ..core import entities
from .widgets.image_viewer import VisorImagen
from .widgets.text_editor import EditorTranscripcion, PalabraIndexada

LEYENDAS_DISPONIBLES = ["[FIRMA]", "[SELLO]", "[RÚBRICA]", "[HUELLA]", "[TEXTO ILEGIBLE]"]


class DialogoBuscarReemplazar(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Buscar y reemplazar")
        layout = QFormLayout(self)
        self.campo_buscar = QLineEdit()
        self.campo_reemplazar = QLineEdit()
        layout.addRow("Buscar:", self.campo_buscar)
        layout.addRow("Reemplazar con:", self.campo_reemplazar)
        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        layout.addRow(botones)


class VistaRevision(QWidget):
    pagina_cambiada = Signal(int)

    def __init__(self, umbral_confianza: int = 85, parent=None):
        super().__init__(parent)
        self._proyecto: Proyecto | None = None
        self._indice_actual = 0
        self._umbral_confianza = umbral_confianza

        layout = QVBoxLayout(self)

        barra_navegacion = QHBoxLayout()
        self.boton_anterior = QPushButton("◀ Página anterior")
        self.boton_siguiente = QPushButton("Página siguiente ▶")
        self.etiqueta_pagina = QLabel("Página 0 de 0")
        self.boton_anterior.clicked.connect(self._ir_anterior)
        self.boton_siguiente.clicked.connect(self._ir_siguiente)
        barra_navegacion.addWidget(self.boton_anterior)
        barra_navegacion.addWidget(self.etiqueta_pagina)
        barra_navegacion.addWidget(self.boton_siguiente)
        barra_navegacion.addStretch()
        layout.addLayout(barra_navegacion)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        panel_izquierdo = QWidget()
        layout_izq = QVBoxLayout(panel_izquierdo)
        barra_imagen = QToolBar()
        self.visor = VisorImagen()
        boton_zoom_mas = QPushButton("Acercar (+)")
        boton_zoom_menos = QPushButton("Alejar (-)")
        boton_girar_izq = QPushButton("Girar izquierda")
        boton_girar_der = QPushButton("Girar derecha")
        boton_zoom_mas.clicked.connect(self.visor.acercar)
        boton_zoom_menos.clicked.connect(self.visor.alejar)
        boton_girar_izq.clicked.connect(lambda: self.visor.girar(-90))
        boton_girar_der.clicked.connect(lambda: self.visor.girar(90))
        for b in (boton_zoom_mas, boton_zoom_menos, boton_girar_izq, boton_girar_der):
            barra_imagen.addWidget(b)
        layout_izq.addWidget(barra_imagen)
        layout_izq.addWidget(self.visor)
        splitter.addWidget(panel_izquierdo)

        panel_derecho = QWidget()
        layout_der = QVBoxLayout(panel_derecho)
        barra_texto = QToolBar()
        boton_deshacer = QPushButton("Deshacer")
        boton_rehacer = QPushButton("Rehacer")
        boton_buscar = QPushButton("Buscar y reemplazar")
        boton_marcar_revisada = QPushButton("Marcar palabra como revisada")
        boton_leyenda = QPushButton("Insertar leyenda ▾")
        menu_leyendas = QMenu(boton_leyenda)
        for leyenda in LEYENDAS_DISPONIBLES:
            accion = menu_leyendas.addAction(leyenda)
            accion.triggered.connect(lambda checked=False, l=leyenda: self._insertar_leyenda(l))
        boton_leyenda.setMenu(menu_leyendas)

        self.editor = EditorTranscripcion()
        boton_deshacer.clicked.connect(self.editor.undo)
        boton_rehacer.clicked.connect(self.editor.redo)
        boton_buscar.clicked.connect(self._abrir_buscar_reemplazar)
        boton_marcar_revisada.clicked.connect(self._marcar_revisada)

        for b in (boton_deshacer, boton_rehacer, boton_buscar, boton_marcar_revisada, boton_leyenda):
            barra_texto.addWidget(b)

        self.etiqueta_advertencia = QLabel("")
        self.etiqueta_advertencia.setStyleSheet("color: #b26a00; font-weight: bold;")
        self.etiqueta_advertencia.setWordWrap(True)

        layout_der.addWidget(barra_texto)
        layout_der.addWidget(self.editor)
        layout_der.addWidget(self.etiqueta_advertencia)
        splitter.addWidget(panel_derecho)

        splitter.setSizes([500, 500])
        layout.addWidget(splitter)

        self.editor.palabra_dudosa_seleccionada.connect(self.visor.resaltar_zona)
        self.editor.textChanged.connect(self._al_cambiar_texto)

    def cargar_proyecto(self, proyecto: Proyecto) -> None:
        self._proyecto = proyecto
        self._indice_actual = 0
        self._mostrar_pagina_actual()

    def establecer_umbral(self, umbral: int) -> None:
        self._umbral_confianza = umbral
        self._mostrar_pagina_actual()

    def _pagina_actual(self) -> PaginaProyecto | None:
        if not self._proyecto or not self._proyecto.paginas:
            return None
        return self._proyecto.paginas[self._indice_actual]

    def _mostrar_pagina_actual(self) -> None:
        pagina = self._pagina_actual()
        if pagina is None:
            return
        total = len(self._proyecto.paginas)
        self.etiqueta_pagina.setText(f"Página {self._indice_actual + 1} de {total}")
        self.boton_anterior.setEnabled(self._indice_actual > 0)
        self.boton_siguiente.setEnabled(self._indice_actual < total - 1)

        if pagina.ruta_imagen_temporal:
            self.visor.cargar_imagen(pagina.ruta_imagen_temporal)

        palabras_indexadas = [
            PalabraIndexada(p.texto, p.confianza, p.x, p.y, p.ancho, p.alto, p.revisada)
            for p in pagina.palabras
            if p.confianza < self._umbral_confianza
        ]
        self.editor.blockSignals(True)
        self.editor.cargar_texto(pagina.texto_corregido, palabras_indexadas)
        self.editor.blockSignals(False)

        if pagina.fallo_procesamiento:
            self.etiqueta_advertencia.setText(
                f"Esta página no pudo procesarse ({pagina.mensaje_error or 'error desconocido'}). "
                "Puede continuar revisando otras páginas y regresar después."
            )
        else:
            advertencias = entities.verificar_consistencia_cantidades(pagina.texto_corregido)
            self.etiqueta_advertencia.setText(" ".join(advertencias))

        self.pagina_cambiada.emit(self._indice_actual)

    def _al_cambiar_texto(self) -> None:
        pagina = self._pagina_actual()
        if pagina is not None:
            pagina.texto_corregido = self.editor.toPlainText()

    def _ir_anterior(self) -> None:
        if self._indice_actual > 0:
            self._indice_actual -= 1
            self._mostrar_pagina_actual()

    def _ir_siguiente(self) -> None:
        if self._proyecto and self._indice_actual < len(self._proyecto.paginas) - 1:
            self._indice_actual += 1
            self._mostrar_pagina_actual()

    def _marcar_revisada(self) -> None:
        if not self.editor.marcar_palabra_actual_como_revisada():
            QMessageBox.information(self, "Marcar como revisada", "Coloque el cursor sobre una palabra resaltada en amarillo.")
        pagina = self._pagina_actual()
        if pagina is not None:
            pagina.revisada = all(p.revisada or p.confianza >= self._umbral_confianza for p in pagina.palabras)

    def _abrir_buscar_reemplazar(self) -> None:
        dialogo = DialogoBuscarReemplazar(self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            buscar = dialogo.campo_buscar.text()
            reemplazar = dialogo.campo_reemplazar.text()
            n = self.editor.reemplazar_todo(buscar, reemplazar)
            QMessageBox.information(self, "Buscar y reemplazar", f"Se reemplazaron {n} coincidencia(s).")

    def _insertar_leyenda(self, leyenda: str) -> None:
        cursor = self.editor.textCursor()
        cursor.insertText(leyenda)
