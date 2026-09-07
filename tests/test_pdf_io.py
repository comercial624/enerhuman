from pathlib import Path

import pytest

from transcriptor_notarial.core import pdf_io
from .conftest import crear_imagen_texto, crear_pdf_desde_imagenes, crear_pdf_con_texto, TEXTO_ACTA_FICTICIA


def test_contar_paginas_pdf_una_pagina(tmp_path: Path):
    ruta_img = crear_imagen_texto(TEXTO_ACTA_FICTICIA, tmp_path / "p1.png")
    ruta_pdf = crear_pdf_desde_imagenes([ruta_img], tmp_path / "doc.pdf")
    assert pdf_io.contar_paginas(ruta_pdf) == 1


def test_contar_paginas_pdf_multiples_paginas(tmp_path: Path):
    rutas_img = [
        crear_imagen_texto(f"Pagina {i}", tmp_path / f"p{i}.png") for i in range(3)
    ]
    ruta_pdf = crear_pdf_desde_imagenes(rutas_img, tmp_path / "doc.pdf")
    assert pdf_io.contar_paginas(ruta_pdf) == 3


def test_pdf_danado_lanza_error(tmp_path: Path):
    ruta = tmp_path / "danado.pdf"
    ruta.write_bytes(b"esto no es un pdf valido")
    with pytest.raises(pdf_io.ArchivoDanadoError):
        pdf_io.contar_paginas(ruta)


def test_pdf_protegido_lanza_error(tmp_path: Path):
    import fitz

    ruta = tmp_path / "protegido.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.save(str(ruta), encryption=fitz.PDF_ENCRYPT_AES_256, user_pw="secreta")
    doc.close()

    with pytest.raises(pdf_io.DocumentoProtegidoError):
        pdf_io.contar_paginas(ruta)


def test_construir_expediente_con_varios_archivos(tmp_path: Path):
    ruta_img1 = crear_imagen_texto("uno", tmp_path / "a.png")
    ruta_pdf = crear_pdf_desde_imagenes(
        [crear_imagen_texto("dos", tmp_path / "b.png"), crear_imagen_texto("tres", tmp_path / "c.png")],
        tmp_path / "doc.pdf",
    )
    paginas = pdf_io.construir_expediente([ruta_img1, ruta_pdf])
    assert len(paginas) == 3
    assert paginas[0].archivo_origen == ruta_img1
    assert paginas[1].archivo_origen == ruta_pdf
    assert paginas[1].indice_pagina_en_archivo == 0
    assert paginas[2].indice_pagina_en_archivo == 1


def test_rasterizar_pagina_imagen_devuelve_bgr(tmp_path: Path):
    ruta_img = crear_imagen_texto(TEXTO_ACTA_FICTICIA, tmp_path / "p1.png")
    pagina = pdf_io.PaginaFuente(ruta_img, 0, 1)
    imagen_bgr, dpi = pdf_io.rasterizar_pagina(pagina)
    assert imagen_bgr.ndim == 3
    assert dpi > 0


def test_extraer_texto_existente_en_pdf_con_texto(tmp_path: Path):
    ruta_pdf = crear_pdf_con_texto("Contenido de prueba sin OCR", tmp_path / "con_texto.pdf")
    pagina = pdf_io.PaginaFuente(ruta_pdf, 0, 1)
    texto = pdf_io.extraer_texto_existente(pagina)
    assert texto is not None
    assert "Contenido de prueba" in texto


def test_extraer_texto_existente_en_pdf_escaneado_devuelve_none(tmp_path: Path):
    ruta_img = crear_imagen_texto(TEXTO_ACTA_FICTICIA, tmp_path / "p1.png")
    ruta_pdf = crear_pdf_desde_imagenes([ruta_img], tmp_path / "escaneado.pdf")
    pagina = pdf_io.PaginaFuente(ruta_pdf, 0, 1)
    assert pdf_io.extraer_texto_existente(pagina) is None


def test_imagen_extension_no_soportada(tmp_path: Path):
    ruta = tmp_path / "archivo.txt"
    ruta.write_text("no es una imagen")
    with pytest.raises(ValueError):
        pdf_io.contar_paginas(ruta)
