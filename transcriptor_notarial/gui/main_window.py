"""Ventana principal de Transcriptor Notarial."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton,
    QProgressBar, QLabel, QFileDialog, QMessageBox, QListWidget,
    QListWidgetItem, QAbstractItemView, QTabWidget, QMenuBar, QInputDialog,
)

from .. import paths, logging_setup
from ..config import GestorConfiguracion
from ..core import pdf_io, docx_export, word_integration, scanner_wia
from ..core.project_store import Proyecto, AlmacenProyectos
from .review_view import VistaRevision
from .config_dialog import DialogoConfiguracion
from .workers import HiloProcesamiento


class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transcriptor Notarial")
        self.resize(1100, 750)

        self._gestor_config = GestorConfiguracion()
        self._almacen_proyectos = AlmacenProyectos()
        self._proyecto: Proyecto | None = None
        self._archivos_seleccionados: list[Path] = []
        self._hilo_procesamiento: HiloProcesamiento | None = None
        self._ruta_docx_generado: Path | None = None

        self._construir_menu()
        self._construir_interfaz()
        self._advertir_si_es_usb()
        self._ofrecer_recuperacion_sesion()

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------
    def _construir_menu(self) -> None:
        barra = self.menuBar()
        menu_archivo = barra.addMenu("Archivo")
        accion_config = QAction("Configuración...", self)
        accion_config.triggered.connect(self._abrir_configuracion)
        menu_archivo.addAction(accion_config)

        accion_copiar_local = QAction("Copiar programa a esta computadora...", self)
        accion_copiar_local.triggered.connect(self._copiar_programa_localmente)
        menu_archivo.addAction(accion_copiar_local)

        accion_salir = QAction("Salir", self)
        accion_salir.triggered.connect(self.close)
        menu_archivo.addAction(accion_salir)

    def _construir_interfaz(self) -> None:
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)

        grilla_botones = QGridLayout()
        self.boton_escanear = QPushButton("Escanear documento")
        self.boton_seleccionar = QPushButton("Seleccionar PDF o imágenes")
        self.boton_agregar = QPushButton("Agregar páginas")
        self.boton_ordenar = QPushButton("Ordenar páginas")
        self.boton_procesar = QPushButton("Procesar documento")
        self.boton_cancelar = QPushButton("Cancelar procesamiento")
        self.boton_revisar = QPushButton("Revisar transcripción")
        self.boton_guardar_word = QPushButton("Guardar en Word")
        self.boton_abrir_word = QPushButton("Abrir en Word")
        self.boton_abrir_carpeta = QPushButton("Abrir carpeta de destino")

        botones = [
            self.boton_escanear, self.boton_seleccionar, self.boton_agregar,
            self.boton_ordenar, self.boton_procesar, self.boton_cancelar,
            self.boton_revisar, self.boton_guardar_word, self.boton_abrir_word,
            self.boton_abrir_carpeta,
        ]
        for i, boton in enumerate(botones):
            grilla_botones.addWidget(boton, i // 5, i % 5)

        self.boton_escanear.clicked.connect(self._escanear_documento)
        self.boton_seleccionar.clicked.connect(self._seleccionar_archivos)
        self.boton_agregar.clicked.connect(self._agregar_paginas)
        self.boton_ordenar.clicked.connect(self._ordenar_paginas)
        self.boton_procesar.clicked.connect(self._procesar_documento)
        self.boton_cancelar.clicked.connect(self._cancelar_procesamiento)
        self.boton_revisar.clicked.connect(self._mostrar_revision)
        self.boton_guardar_word.clicked.connect(self._guardar_en_word)
        self.boton_abrir_word.clicked.connect(self._abrir_en_word)
        self.boton_abrir_carpeta.clicked.connect(self._abrir_carpeta_destino)

        self.boton_cancelar.setEnabled(False)
        self.boton_revisar.setEnabled(False)
        self.boton_guardar_word.setEnabled(False)
        self.boton_abrir_word.setEnabled(False)

        layout.addLayout(grilla_botones)

        self.lista_paginas = QListWidget()
        self.lista_paginas.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.lista_paginas.setToolTip("Orden de las páginas del expediente antes de procesar. Arrastre para reordenar.")
        layout.addWidget(QLabel("Páginas del expediente:"))
        layout.addWidget(self.lista_paginas)

        barra_progreso_layout = QHBoxLayout()
        self.barra_progreso = QProgressBar()
        self.etiqueta_estado = QLabel("Listo.")
        barra_progreso_layout.addWidget(self.barra_progreso)
        layout.addLayout(barra_progreso_layout)
        layout.addWidget(self.etiqueta_estado)

        self.pestanas = QTabWidget()
        self.vista_revision = VistaRevision(umbral_confianza=self._gestor_config.config.umbral_baja_confianza)
        self.pestanas.addTab(QWidget(), "Inicio")
        self.pestanas.addTab(self.vista_revision, "Revisión")
        layout.addWidget(self.pestanas)

        self.setCentralWidget(contenedor)

    # ------------------------------------------------------------------
    # Advertencias de entorno (USB, sesión anterior)
    # ------------------------------------------------------------------
    def _advertir_si_es_usb(self) -> None:
        if paths.is_running_from_removable_drive():
            QMessageBox.warning(
                self, "Memoria USB detectada",
                "El programa se está ejecutando desde una memoria USB u otra "
                "unidad extraíble.\n\nNo retire la unidad mientras el programa "
                "esté abierto o mientras se esté procesando un documento: "
                "podría perder trabajo no guardado."
            )

    def _ofrecer_recuperacion_sesion(self) -> None:
        pendientes = self._almacen_proyectos.listar_proyectos_sin_cerrar()
        if not pendientes:
            return
        respuesta = QMessageBox.question(
            self, "Recuperar sesión",
            f"Se encontró {len(pendientes)} expediente(s) de una sesión que no "
            "se cerró correctamente. ¿Desea recuperar el más reciente?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if respuesta == QMessageBox.StandardButton.Yes:
            proyecto = sorted(pendientes, key=lambda p: p.modificado_en)[-1]
            self._proyecto = proyecto
            self._refrescar_lista_paginas_desde_proyecto()
            self.boton_revisar.setEnabled(True)
            self.boton_guardar_word.setEnabled(True)

    # ------------------------------------------------------------------
    # Selección / escaneo de páginas
    # ------------------------------------------------------------------
    def _seleccionar_archivos(self) -> None:
        filtro = "Documentos soportados (*.pdf *.jpg *.jpeg *.png *.tif *.tiff)"
        carpeta_inicial = self._gestor_config.config.carpeta_entrada_predeterminada or ""
        rutas, _ = QFileDialog.getOpenFileNames(self, "Seleccionar PDF o imágenes", carpeta_inicial, filtro)
        if not rutas:
            return
        self._archivos_seleccionados = [Path(r) for r in rutas]
        self._refrescar_lista_paginas_desde_archivos()

    def _agregar_paginas(self) -> None:
        filtro = "Documentos soportados (*.pdf *.jpg *.jpeg *.png *.tif *.tiff)"
        rutas, _ = QFileDialog.getOpenFileNames(self, "Agregar páginas", "", filtro)
        if not rutas:
            return
        self._archivos_seleccionados.extend(Path(r) for r in rutas)
        self._refrescar_lista_paginas_desde_archivos()

    def _ordenar_paginas(self) -> None:
        QMessageBox.information(
            self, "Ordenar páginas",
            "Arrastre los elementos de la lista de páginas para cambiar su orden "
            "antes de presionar 'Procesar documento'."
        )

    def _escanear_documento(self) -> None:
        if not scanner_wia.wia_disponible():
            QMessageBox.warning(
                self, "Escáner no disponible",
                "El escaneo directo (WIA) solo está disponible en Windows con un "
                "escáner y controlador instalados. Use 'Seleccionar PDF o imágenes' "
                "para continuar con archivos ya digitalizados."
            )
            return
        dispositivos = scanner_wia.listar_escaneres()
        if not dispositivos:
            QMessageBox.warning(self, "Sin escáner", "No se detectó ningún escáner conectado.")
            return
        try:
            carpeta_temp = paths.temp_root_dir() / "escaneos"
            carpeta_temp.mkdir(parents=True, exist_ok=True)
            ruta_salida = carpeta_temp / f"escaneo_{len(self._archivos_seleccionados) + 1}.png"
            scanner_wia.escanear_pagina(
                dispositivos[0].id_dispositivo, ruta_salida,
                dpi=self._gestor_config.config.resolucion_escaner_dpi,
                color=self._gestor_config.config.escaneo_color,
            )
            self._archivos_seleccionados.append(ruta_salida)
            self._refrescar_lista_paginas_desde_archivos()
        except scanner_wia.EscanerNoDisponibleError as e:
            QMessageBox.critical(self, "Error de escaneo", str(e))

    def _refrescar_lista_paginas_desde_archivos(self) -> None:
        self.lista_paginas.clear()
        try:
            paginas = pdf_io.construir_expediente(self._archivos_seleccionados)
        except (pdf_io.DocumentoProtegidoError, pdf_io.ArchivoDanadoError) as e:
            QMessageBox.critical(self, "Error al leer el archivo", str(e))
            return
        for pagina in paginas:
            self.lista_paginas.addItem(QListWidgetItem(pagina.etiqueta))
        self.etiqueta_estado.setText(f"{len(paginas)} página(s) lista(s) para procesar.")

    def _refrescar_lista_paginas_desde_proyecto(self) -> None:
        self.lista_paginas.clear()
        if not self._proyecto:
            return
        for pagina in self._proyecto.paginas:
            estado = "✔ revisada" if pagina.revisada else ("✖ error" if pagina.fallo_procesamiento else "pendiente")
            self.lista_paginas.addItem(QListWidgetItem(f"Página {pagina.numero} — {estado}"))

    # ------------------------------------------------------------------
    # Procesamiento
    # ------------------------------------------------------------------
    def _procesar_documento(self) -> None:
        if not self._archivos_seleccionados:
            QMessageBox.warning(self, "Sin archivos", "Seleccione o escanee al menos un documento primero.")
            return

        if paths.is_running_from_removable_drive():
            respuesta = QMessageBox.question(
                self, "Unidad extraíble",
                "El programa se ejecuta desde una memoria USB. No retire la unidad "
                "durante el procesamiento. ¿Desea continuar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if respuesta != QMessageBox.StandardButton.Yes:
                return

        try:
            paginas_fuente = pdf_io.construir_expediente(self._archivos_seleccionados)
        except (pdf_io.DocumentoProtegidoError, pdf_io.ArchivoDanadoError) as e:
            QMessageBox.critical(self, "Error al leer el archivo", str(e))
            return

        nombre, ok = QInputDialog.getText(self, "Nombre del expediente", "Nombre para identificar este expediente:")
        if not ok:
            return

        self._proyecto = Proyecto(
            nombre=nombre or "Expediente sin título",
            archivos_origen=[str(a) for a in self._archivos_seleccionados],
            idioma_ocr=self._gestor_config.config.idioma_ocr,
        )
        carpeta_temp = paths.temp_root_dir() / self._proyecto.id
        self._almacen_proyectos.guardar(self._proyecto)

        self._hilo_procesamiento = HiloProcesamiento(
            paginas_fuente, self._gestor_config.config.idioma_ocr,
            carpeta_temp, self._proyecto, self._almacen_proyectos,
        )
        self._hilo_procesamiento.progreso.connect(self._al_recibir_progreso)
        self._hilo_procesamiento.finalizado.connect(self._al_finalizar_procesamiento)
        self._hilo_procesamiento.error_fatal.connect(self._al_ocurrir_error_fatal)

        self.boton_procesar.setEnabled(False)
        self.boton_cancelar.setEnabled(True)
        self._hilo_procesamiento.start()

    def _cancelar_procesamiento(self) -> None:
        if self._hilo_procesamiento:
            self._hilo_procesamiento.solicitar_cancelacion()
            self.etiqueta_estado.setText("Cancelando... se detendrá después de la página en curso.")

    def _al_recibir_progreso(self, progreso) -> None:
        self.barra_progreso.setMaximum(max(progreso.total_paginas, 1))
        self.barra_progreso.setValue(progreso.pagina_actual)
        texto_estado = {
            "preparando_imagen": "Preparando imagen",
            "reconociendo_texto": "Reconociendo texto",
            "creando_word": "Creando Word",
            "finalizado": "Finalizado",
            "cancelado": "Cancelado",
        }.get(progreso.estado.value, progreso.estado.value)
        eta = ""
        if progreso.tiempo_restante_estimado_s:
            minutos = int(progreso.tiempo_restante_estimado_s // 60)
            segundos = int(progreso.tiempo_restante_estimado_s % 60)
            eta = f" — tiempo restante estimado: {minutos:02d}:{segundos:02d}"
        self.etiqueta_estado.setText(
            f"{texto_estado} ({progreso.pagina_actual}/{progreso.total_paginas}, "
            f"{progreso.porcentaje:.0f}%) {progreso.etiqueta_pagina}{eta}"
        )

    def _al_finalizar_procesamiento(self, proyecto: Proyecto) -> None:
        self._proyecto = proyecto
        self.boton_procesar.setEnabled(True)
        self.boton_cancelar.setEnabled(False)
        self.boton_revisar.setEnabled(True)
        self.boton_guardar_word.setEnabled(True)
        self._refrescar_lista_paginas_desde_proyecto()
        fallidas = sum(1 for p in proyecto.paginas if p.fallo_procesamiento)
        mensaje = "Procesamiento finalizado."
        if fallidas:
            mensaje += f" {fallidas} página(s) tuvieron un error y quedaron marcadas para revisión."
        self.etiqueta_estado.setText(mensaje)
        QMessageBox.information(self, "Procesamiento finalizado", mensaje)

    def _al_ocurrir_error_fatal(self, mensaje: str) -> None:
        self.boton_procesar.setEnabled(True)
        self.boton_cancelar.setEnabled(False)
        QMessageBox.critical(self, "Error durante el procesamiento", mensaje)

    # ------------------------------------------------------------------
    # Revisión y exportación
    # ------------------------------------------------------------------
    def _mostrar_revision(self) -> None:
        if not self._proyecto:
            return
        self.vista_revision.establecer_umbral(self._gestor_config.config.umbral_baja_confianza)
        self.vista_revision.cargar_proyecto(self._proyecto)
        self.pestanas.setCurrentWidget(self.vista_revision)

    def _guardar_en_word(self) -> None:
        if not self._proyecto:
            return
        carpeta_salida = Path(self._gestor_config.config.carpeta_salida_predeterminada)
        try:
            carpeta_salida.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            QMessageBox.critical(self, "Sin permiso para guardar", f"No se pudo crear/usar la carpeta de salida: {e}")
            return

        nombre_archivo = f"{self._proyecto.nombre}.docx".replace("/", "-")
        ruta_sugerida = carpeta_salida / nombre_archivo
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar en Word", str(ruta_sugerida), "Documentos Word (*.docx)"
        )
        if not ruta:
            return

        paginas_transcritas = [
            docx_export.PaginaTranscrita(numero=p.numero, texto=p.texto_corregido)
            for p in self._proyecto.paginas
        ]
        plantilla = self._gestor_config.config.plantilla_word_predeterminada
        ruta_plantilla = Path(plantilla) if plantilla else None

        try:
            self._ruta_docx_generado = docx_export.generar_documento(
                paginas_transcritas, self._gestor_config.config, Path(ruta),
                ruta_plantilla=ruta_plantilla,
            )
        except PermissionError:
            QMessageBox.critical(self, "Sin permiso", "No se tiene permiso para guardar en la carpeta seleccionada.")
            return
        except OSError as e:
            QMessageBox.critical(self, "Error al guardar", f"No se pudo guardar el archivo: {e}")
            return

        self.boton_abrir_word.setEnabled(True)
        self._almacen_proyectos.marcar_cerrado_correctamente(self._proyecto)
        QMessageBox.information(self, "Documento guardado", f"El documento se guardó en:\n{self._ruta_docx_generado}")

        if self._gestor_config.config.abrir_word_automaticamente:
            self._abrir_en_word()

    def _abrir_en_word(self) -> None:
        if not self._ruta_docx_generado:
            return
        try:
            word_integration.abrir_documento(self._ruta_docx_generado)
        except (word_integration.WordNoDisponibleError, FileNotFoundError) as e:
            QMessageBox.warning(self, "No se pudo abrir Word", str(e))

    def _abrir_carpeta_destino(self) -> None:
        carpeta = Path(self._gestor_config.config.carpeta_salida_predeterminada)
        carpeta.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(str(carpeta))  # type: ignore[attr-defined]
        except AttributeError:
            import subprocess
            subprocess.run(["xdg-open", str(carpeta)], check=False)

    # ------------------------------------------------------------------
    # Configuración y copia local
    # ------------------------------------------------------------------
    def _abrir_configuracion(self) -> None:
        dialogo = DialogoConfiguracion(self._gestor_config, self)
        dialogo.exec()

    def _copiar_programa_localmente(self) -> None:
        destino = paths.app_local_copy_dir()
        respuesta = QMessageBox.question(
            self, "Copiar programa a esta computadora",
            f"Se copiará el programa a:\n{destino}\n\n"
            "Esto no requiere permisos de administrador. ¿Desea continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if respuesta != QMessageBox.StandardButton.Yes:
            return
        origen = paths.app_base_dir()
        try:
            shutil.copytree(origen, destino, dirs_exist_ok=True)
        except OSError as e:
            QMessageBox.critical(self, "Error al copiar", str(e))
            return
        QMessageBox.information(
            self, "Copia completa",
            f"El programa se copió a:\n{destino}\n\n"
            "Puede crear accesos directos manualmente desde esa carpeta."
        )

    # ------------------------------------------------------------------
    def closeEvent(self, event) -> None:
        if self._proyecto:
            self._almacen_proyectos.marcar_cerrado_correctamente(self._proyecto)
        if self._gestor_config.config.eliminar_temporales_al_cerrar:
            carpeta_temp = paths.temp_root_dir()
            try:
                shutil.rmtree(carpeta_temp, ignore_errors=True)
            except OSError:
                pass
        super().closeEvent(event)
