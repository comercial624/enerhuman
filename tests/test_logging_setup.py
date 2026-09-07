from pathlib import Path

from transcriptor_notarial import logging_setup


def test_no_guarda_contenido_del_documento(tmp_path, monkeypatch):
    monkeypatch.setattr(logging_setup, "_logger", None)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    texto_confidencial = "Juan Perez Gonzalez vive en Calle Falsa 123, CURP ABCD010101HDFXXX01"
    logging_setup.registrar_evento("procesar_documento", duracion_segundos=1.2, num_paginas=3)

    ruta_log = tmp_path / logging_setup.paths.APP_NAME / "logs" / "tecnico.log"
    contenido = ruta_log.read_text(encoding="utf-8")
    assert texto_confidencial not in contenido
    assert "procesar_documento" in contenido
    assert "paginas=3" in contenido


def test_mensaje_largo_se_trunca(tmp_path, monkeypatch):
    monkeypatch.setattr(logging_setup, "_logger", None)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    texto_largo = "A" * 5000
    logging_setup.registrar_evento(texto_largo)

    ruta_log = tmp_path / logging_setup.paths.APP_NAME / "logs" / "tecnico.log"
    contenido = ruta_log.read_text(encoding="utf-8")
    assert len(contenido) < 5000


def test_borrar_historial_elimina_archivo(tmp_path, monkeypatch):
    monkeypatch.setattr(logging_setup, "_logger", None)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    logging_setup.registrar_evento("prueba")
    ruta_log = tmp_path / logging_setup.paths.APP_NAME / "logs" / "tecnico.log"
    assert ruta_log.exists()

    logging_setup.borrar_historial()
    assert not ruta_log.exists()
