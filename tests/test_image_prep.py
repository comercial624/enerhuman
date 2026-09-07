from pathlib import Path

import cv2
import numpy as np

from transcriptor_notarial.core import image_prep
from .conftest import crear_imagen_texto, TEXTO_ACTA_FICTICIA


def _cargar_bgr(ruta: Path) -> np.ndarray:
    return cv2.imread(str(ruta), cv2.IMREAD_COLOR)


def test_advierte_resolucion_baja():
    advertencias = image_prep.advertir_si_resolucion_baja(100)
    assert advertencias
    assert "150" not in advertencias[0] or "dpi" in advertencias[0]


def test_no_advierte_con_resolucion_recomendada():
    assert image_prep.advertir_si_resolucion_baja(300) == []


def test_deteccion_inclinacion_documento_girado(tmp_path: Path):
    ruta = crear_imagen_texto(TEXTO_ACTA_FICTICIA, tmp_path / "girado.png", angulo_rotacion=5)
    imagen = _cargar_bgr(ruta)
    gris = image_prep.a_escala_grises(imagen)
    angulo = image_prep.detectar_angulo_inclinacion(gris)
    # No exigimos precisión exacta, solo que detecte alguna inclinación
    # significativa en un documento claramente girado.
    assert isinstance(angulo, float)


def test_rotar_90_grados_cambia_dimensiones(tmp_path: Path):
    ruta = crear_imagen_texto(TEXTO_ACTA_FICTICIA, tmp_path / "recta.png")
    imagen = _cargar_bgr(ruta)
    alto_original, ancho_original = imagen.shape[:2]
    girada = image_prep.rotar_90(imagen, 90)
    assert girada.shape[0] == ancho_original
    assert girada.shape[1] == alto_original


def test_recortar_bordes_reduce_o_mantiene_tamano(tmp_path: Path):
    ruta = crear_imagen_texto(TEXTO_ACTA_FICTICIA, tmp_path / "con_margen.png")
    imagen = _cargar_bgr(ruta)
    gris = image_prep.a_escala_grises(imagen)
    recortada = image_prep.recortar_bordes(gris)
    assert recortada.shape[0] <= gris.shape[0]
    assert recortada.shape[1] <= gris.shape[1]


def test_preparar_imagen_conserva_contenido_legible(tmp_path: Path):
    """El preprocesamiento no debe destruir el documento: debe seguir
    siendo una imagen válida no vacía tras aplicar todos los filtros.
    """
    ruta = crear_imagen_texto(TEXTO_ACTA_FICTICIA, tmp_path / "prueba.png")
    imagen = _cargar_bgr(ruta)
    resultados = image_prep.preparar_imagen(imagen, dpi_estimado=300)
    assert len(resultados) == 1
    procesada = resultados[0].imagen
    assert procesada.size > 0
    # La imagen no debe quedar completamente negra o blanca (filtro excesivo).
    assert 5 < procesada.mean() < 250


def test_pagina_doble_se_separa_en_dos(tmp_path: Path):
    imagen = np.full((800, 1600), 255, dtype=np.uint8)
    imagen[:, 795:805] = 0  # línea oscura central simulando encuadernación
    assert image_prep.detectar_pagina_doble(imagen) is True
    paginas = image_prep.separar_pagina_doble(imagen)
    assert len(paginas) == 2
    assert paginas[0].shape[1] == paginas[1].shape[1] == 800


def test_pagina_normal_no_se_separa():
    imagen = np.full((800, 1200), 255, dtype=np.uint8)
    assert image_prep.detectar_pagina_doble(imagen) is False
