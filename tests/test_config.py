from pathlib import Path

from transcriptor_notarial.config import ConfiguracionApp, GestorConfiguracion


def test_valores_predeterminados_razonables():
    c = ConfiguracionApp()
    assert c.resolucion_escaner_dpi == 300
    assert c.idioma_ocr == "spa"
    assert c.umbral_baja_confianza == 85
    assert c.fuente_word == "Arial"
    assert c.tamano_letra == 12
    assert c.alineacion == "justificado"


def test_guardar_y_recargar_configuracion(tmp_path: Path):
    ruta = tmp_path / "config.json"
    gestor = GestorConfiguracion(ruta_archivo=ruta)
    gestor.actualizar(idioma_ocr="spa+eng", umbral_baja_confianza=70)

    gestor2 = GestorConfiguracion(ruta_archivo=ruta)
    assert gestor2.config.idioma_ocr == "spa+eng"
    assert gestor2.config.umbral_baja_confianza == 70


def test_configuracion_corrupta_usa_predeterminados(tmp_path: Path):
    ruta = tmp_path / "config.json"
    ruta.write_text("{ esto no es json valido ")
    gestor = GestorConfiguracion(ruta_archivo=ruta)
    assert gestor.config.idioma_ocr == "spa"


def test_restaurar_predeterminados(tmp_path: Path):
    ruta = tmp_path / "config.json"
    gestor = GestorConfiguracion(ruta_archivo=ruta)
    gestor.actualizar(umbral_baja_confianza=10)
    gestor.restaurar_predeterminados()
    assert gestor.config.umbral_baja_confianza == 85


def test_campos_desconocidos_en_json_se_ignoran(tmp_path: Path):
    import json
    ruta = tmp_path / "config.json"
    ruta.write_text(json.dumps({"idioma_ocr": "spa", "campo_futuro_desconocido": 123}))
    gestor = GestorConfiguracion(ruta_archivo=ruta)
    assert gestor.config.idioma_ocr == "spa"
