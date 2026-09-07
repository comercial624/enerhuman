import shutil
from pathlib import Path

import cv2
import pytest

from transcriptor_notarial.core import ocr_engine
from .conftest import crear_imagen_texto, TEXTO_ACTA_FICTICIA

TESSERACT_DISPONIBLE = shutil.which("tesseract") is not None

pytestmark = pytest.mark.skipif(
    not TESSERACT_DISPONIBLE, reason="Tesseract no está instalado en este entorno."
)


def test_configurar_tesseract_no_lanza_si_esta_instalado():
    ocr_engine.configurar_tesseract()  # no debe lanzar excepción


def test_idioma_no_disponible_lanza_error():
    with pytest.raises(ocr_engine.IdiomaNoDisponibleError):
        ocr_engine.reconocer_pagina(
            cv2.imread(str(_imagen_prueba())), idioma="xx_idioma_inexistente"
        )


_RUTA_IMAGEN_CACHE: Path | None = None


def _imagen_prueba() -> Path:
    global _RUTA_IMAGEN_CACHE
    if _RUTA_IMAGEN_CACHE is None:
        import tempfile
        carpeta = Path(tempfile.mkdtemp())
        _RUTA_IMAGEN_CACHE = crear_imagen_texto(TEXTO_ACTA_FICTICIA, carpeta / "prueba.png", tamano_fuente=36)
    return _RUTA_IMAGEN_CACHE


def test_reconoce_texto_en_espanol():
    ruta = _imagen_prueba()
    imagen = cv2.imread(str(ruta), cv2.IMREAD_GRAYSCALE)
    resultado = ocr_engine.reconocer_pagina(imagen, idioma="spa")

    texto_normalizado = resultado.texto_completo.upper()
    assert "ESCRITURA" in texto_normalizado
    assert "NOTARIO" in texto_normalizado


def test_devuelve_palabras_con_coordenadas_y_confianza():
    ruta = _imagen_prueba()
    imagen = cv2.imread(str(ruta), cv2.IMREAD_GRAYSCALE)
    resultado = ocr_engine.reconocer_pagina(imagen, idioma="spa")

    assert len(resultado.palabras) > 0
    primera = resultado.palabras[0]
    assert primera.ancho > 0 and primera.alto > 0
    assert 0 <= primera.confianza <= 100
    assert primera.num_pagina == 1


def test_texto_no_se_corrige_automaticamente():
    """El OCR no debe alterar cantidades ni nombres: se compara que el
    texto reconocido para una cifra específica se mantenga reconocible,
    sin que el motor la reemplace por otra.
    """
    ruta = _imagen_prueba()
    imagen = cv2.imread(str(ruta), cv2.IMREAD_GRAYSCALE)
    resultado = ocr_engine.reconocer_pagina(imagen, idioma="spa")
    # La cantidad "120.50" debe aparecer en alguna palabra reconocida,
    # no una cantidad inventada distinta.
    assert any("120" in p.texto for p in resultado.palabras)
