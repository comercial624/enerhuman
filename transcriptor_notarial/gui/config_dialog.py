"""Cuadro de diálogo de configuración."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox,
    QCheckBox, QPushButton, QHBoxLayout, QVBoxLayout, QFileDialog, QLabel,
    QGroupBox, QMessageBox,
)

from ..config import GestorConfiguracion
from ..core import ocr_engine
from .. import logging_setup


class DialogoConfiguracion(QDialog):
    def __init__(self, gestor: GestorConfiguracion, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración")
        self.setMinimumWidth(480)
        self._gestor = gestor
        c = gestor.config

        layout_general = QVBoxLayout(self)

        grupo_carpetas = QGroupBox("Carpetas")
        f1 = QFormLayout(grupo_carpetas)
        self.campo_entrada = self._campo_con_boton_carpeta(c.carpeta_entrada_predeterminada)
        self.campo_salida = self._campo_con_boton_carpeta(c.carpeta_salida_predeterminada)
        f1.addRow("Carpeta de entrada predeterminada:", self.campo_entrada)
        f1.addRow("Carpeta de salida predeterminada:", self.campo_salida)
        layout_general.addWidget(grupo_carpetas)

        grupo_escaner = QGroupBox("Escáner")
        f2 = QFormLayout(grupo_escaner)
        self.spin_dpi = QSpinBox()
        self.spin_dpi.setRange(75, 1200)
        self.spin_dpi.setValue(c.resolucion_escaner_dpi)
        self.check_color = QCheckBox("Escanear a color (desmarcado = escala de grises)")
        self.check_color.setChecked(c.escaneo_color)
        f2.addRow("Resolución (dpi):", self.spin_dpi)
        f2.addRow(self.check_color)
        layout_general.addWidget(grupo_escaner)

        grupo_ocr = QGroupBox("Reconocimiento OCR")
        f3 = QFormLayout(grupo_ocr)
        self.combo_idioma = QComboBox()
        for codigo, etiqueta in ocr_engine.IDIOMAS_SOPORTADOS.items():
            self.combo_idioma.addItem(etiqueta, codigo)
        indice = self.combo_idioma.findData(c.idioma_ocr)
        if indice >= 0:
            self.combo_idioma.setCurrentIndex(indice)
        self.spin_umbral = QSpinBox()
        self.spin_umbral.setRange(0, 100)
        self.spin_umbral.setSuffix(" %")
        self.spin_umbral.setValue(c.umbral_baja_confianza)
        f3.addRow("Idioma:", self.combo_idioma)
        f3.addRow("Umbral de baja confianza:", self.spin_umbral)
        layout_general.addWidget(grupo_ocr)

        grupo_word = QGroupBox("Documento Word")
        f4 = QFormLayout(grupo_word)
        self.campo_fuente = QLineEdit(c.fuente_word)
        self.spin_tamano = QSpinBox()
        self.spin_tamano.setRange(6, 48)
        self.spin_tamano.setValue(c.tamano_letra)
        self.combo_alineacion = QComboBox()
        self.combo_alineacion.addItems(["justificado", "izquierda", "centrado"])
        self.combo_alineacion.setCurrentText(c.alineacion)
        self.spin_interlineado = QDoubleSpinBox()
        self.spin_interlineado.setRange(1.0, 3.0)
        self.spin_interlineado.setSingleStep(0.05)
        self.spin_interlineado.setValue(c.interlineado)
        self.spin_margen_sup = QDoubleSpinBox(); self.spin_margen_sup.setRange(0, 10); self.spin_margen_sup.setValue(c.margen_superior_cm)
        self.spin_margen_inf = QDoubleSpinBox(); self.spin_margen_inf.setRange(0, 10); self.spin_margen_inf.setValue(c.margen_inferior_cm)
        self.spin_margen_izq = QDoubleSpinBox(); self.spin_margen_izq.setRange(0, 10); self.spin_margen_izq.setValue(c.margen_izquierdo_cm)
        self.spin_margen_der = QDoubleSpinBox(); self.spin_margen_der.setRange(0, 10); self.spin_margen_der.setValue(c.margen_derecho_cm)
        self.check_numeracion = QCheckBox("Numeración de páginas")
        self.check_numeracion.setChecked(c.numeracion_paginas)
        self.campo_plantilla = self._campo_con_boton_archivo(c.plantilla_word_predeterminada, "Documentos Word (*.docx)")

        f4.addRow("Fuente:", self.campo_fuente)
        f4.addRow("Tamaño de letra:", self.spin_tamano)
        f4.addRow("Alineación:", self.combo_alineacion)
        f4.addRow("Interlineado:", self.spin_interlineado)
        f4.addRow("Margen superior (cm):", self.spin_margen_sup)
        f4.addRow("Margen inferior (cm):", self.spin_margen_inf)
        f4.addRow("Margen izquierdo (cm):", self.spin_margen_izq)
        f4.addRow("Margen derecho (cm):", self.spin_margen_der)
        f4.addRow(self.check_numeracion)
        f4.addRow("Plantilla predeterminada:", self.campo_plantilla)
        layout_general.addWidget(grupo_word)

        grupo_comportamiento = QGroupBox("Comportamiento")
        f5 = QFormLayout(grupo_comportamiento)
        self.check_borrar_temp = QCheckBox("Eliminar archivos temporales al cerrar")
        self.check_borrar_temp.setChecked(c.eliminar_temporales_al_cerrar)
        self.check_abrir_word = QCheckBox("Abrir automáticamente el Word terminado")
        self.check_abrir_word.setChecked(c.abrir_word_automaticamente)
        f5.addRow(self.check_borrar_temp)
        f5.addRow(self.check_abrir_word)
        layout_general.addWidget(grupo_comportamiento)

        grupo_privacidad = QGroupBox("Privacidad")
        f6 = QVBoxLayout(grupo_privacidad)
        boton_borrar_historial = QPushButton("Borrar historial técnico")
        boton_borrar_historial.clicked.connect(self._borrar_historial)
        f6.addWidget(boton_borrar_historial)
        layout_general.addWidget(grupo_privacidad)

        botones = QHBoxLayout()
        boton_restaurar = QPushButton("Restaurar valores predeterminados")
        boton_restaurar.clicked.connect(self._restaurar)
        boton_guardar = QPushButton("Guardar")
        boton_guardar.clicked.connect(self._guardar)
        boton_cancelar = QPushButton("Cancelar")
        boton_cancelar.clicked.connect(self.reject)
        botones.addWidget(boton_restaurar)
        botones.addStretch()
        botones.addWidget(boton_guardar)
        botones.addWidget(boton_cancelar)
        layout_general.addLayout(botones)

    def _campo_con_boton_carpeta(self, valor_inicial: str) -> QLineEdit:
        campo = QLineEdit(valor_inicial)
        return campo  # el botón de selección se agrega en un contenedor si se requiere más adelante

    def _campo_con_boton_archivo(self, valor_inicial: str, filtro: str) -> QLineEdit:
        campo = QLineEdit(valor_inicial)
        return campo

    def _borrar_historial(self) -> None:
        logging_setup.borrar_historial()
        QMessageBox.information(self, "Privacidad", "El historial técnico se eliminó correctamente.")

    def _restaurar(self) -> None:
        self._gestor.restaurar_predeterminados()
        QMessageBox.information(self, "Configuración", "Se restauraron los valores predeterminados. Cierre y abra este cuadro de nuevo para verlos.")

    def _guardar(self) -> None:
        self._gestor.actualizar(
            carpeta_entrada_predeterminada=self.campo_entrada.text(),
            carpeta_salida_predeterminada=self.campo_salida.text(),
            resolucion_escaner_dpi=self.spin_dpi.value(),
            escaneo_color=self.check_color.isChecked(),
            idioma_ocr=self.combo_idioma.currentData(),
            umbral_baja_confianza=self.spin_umbral.value(),
            fuente_word=self.campo_fuente.text(),
            tamano_letra=self.spin_tamano.value(),
            alineacion=self.combo_alineacion.currentText(),
            interlineado=self.spin_interlineado.value(),
            margen_superior_cm=self.spin_margen_sup.value(),
            margen_inferior_cm=self.spin_margen_inf.value(),
            margen_izquierdo_cm=self.spin_margen_izq.value(),
            margen_derecho_cm=self.spin_margen_der.value(),
            numeracion_paginas=self.check_numeracion.isChecked(),
            plantilla_word_predeterminada=self.campo_plantilla.text(),
            eliminar_temporales_al_cerrar=self.check_borrar_temp.isChecked(),
            abrir_word_automaticamente=self.check_abrir_word.isChecked(),
        )
        self.accept()
