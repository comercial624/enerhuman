"""Punto de entrada de la aplicación."""
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from . import paths
from .core import ocr_engine


def verificar_requisitos_minimos() -> str | None:
    """Verifica requisitos indispensables antes de mostrar la ventana
    principal. Devuelve un mensaje de error si algo crítico falta, o None
    si se puede continuar (algunas funciones, como el escáner, son
    opcionales y no bloquean el arranque).
    """
    try:
        ocr_engine.configurar_tesseract()
    except ocr_engine.TesseractNoEncontradoError as e:
        return str(e)
    return None


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("TranscriptorNotarial")
    app.setOrganizationName("Notaria")

    error = verificar_requisitos_minimos()
    if error:
        QMessageBox.critical(None, "No se puede iniciar", error)
        return 1

    from .gui.main_window import VentanaPrincipal
    ventana = VentanaPrincipal()
    ventana.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
