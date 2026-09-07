import os
from pathlib import Path

from transcriptor_notarial import paths


def test_app_base_dir_no_depende_del_directorio_actual(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    base = paths.app_base_dir()
    assert base.exists()


def test_local_appdata_usa_variable_de_entorno_si_existe(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    resultado = paths.local_appdata_dir()
    assert resultado == tmp_path / paths.APP_NAME


def test_temporales_no_viven_dentro_de_la_carpeta_de_la_app(monkeypatch, tmp_path):
    """La carpeta temporal debe calcularse desde TEMP/LOCALAPPDATA, nunca
    como subcarpeta de app_base_dir(), para no dejar temporales en la USB.
    """
    carpeta_usb_simulada = tmp_path / "USB" / "Transcriptor_Notarial_Portable"
    carpeta_usb_simulada.mkdir(parents=True)
    carpeta_temp_local = tmp_path / "TempLocal"
    monkeypatch.setenv("TEMP", str(carpeta_temp_local))
    monkeypatch.setattr(paths, "app_base_dir", lambda: carpeta_usb_simulada)

    resultado = paths.temp_root_dir()
    assert carpeta_usb_simulada not in resultado.parents
    assert resultado != carpeta_usb_simulada


def test_no_falla_en_sistema_no_windows_al_detectar_usb():
    # En Linux (entorno de pruebas) siempre debe devolver False, sin excepción.
    assert paths.is_running_from_removable_drive() is False


def test_config_file_path_dentro_de_config_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    ruta = paths.config_file_path()
    assert ruta.parent.exists()
    assert ruta.name == "configuracion.json"


def test_rutas_recursos_relativas_a_app_base_dir():
    assert paths.resources_dir() == paths.app_base_dir() / "recursos"
    assert paths.tesseract_exe_path() == paths.resources_dir() / "tesseract" / "tesseract.exe"
    assert paths.tesseract_tessdata_dir() == paths.resources_dir() / "tesseract" / "tessdata"
