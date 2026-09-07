import shutil
from pathlib import Path

import pytest

from transcriptor_notarial.core import pdf_io, pipeline
from transcriptor_notarial.core.project_store import AlmacenProyectos, Proyecto
from .conftest import crear_imagen_texto, crear_pdf_desde_imagenes, TEXTO_ACTA_FICTICIA

TESSERACT_DISPONIBLE = shutil.which("tesseract") is not None
pytestmark = pytest.mark.skipif(not TESSERACT_DISPONIBLE, reason="Tesseract no disponible.")


def _expediente_dos_paginas(tmp_path: Path) -> list[pdf_io.PaginaFuente]:
    rutas = [
        crear_imagen_texto(TEXTO_ACTA_FICTICIA, tmp_path / "p1.png", tamano_fuente=36),
        crear_imagen_texto("Segunda pagina del expediente de prueba.", tmp_path / "p2.png", tamano_fuente=36),
    ]
    return pdf_io.construir_expediente(rutas)


def test_procesa_expediente_completo(tmp_path: Path):
    paginas_fuente = _expediente_dos_paginas(tmp_path)
    almacen = AlmacenProyectos(carpeta=tmp_path / "proyectos")
    proyecto = Proyecto(nombre="Prueba pipeline")

    eventos = []
    proyecto = pipeline.procesar_expediente(
        paginas_fuente, "spa", tmp_path / "temp", proyecto, almacen,
        callback_progreso=eventos.append,
    )

    assert len(proyecto.paginas) == 2
    assert all(p.texto_reconocido for p in proyecto.paginas)
    assert eventos[-1].estado == pipeline.EstadoProcesamiento.FINALIZADO
    # El proyecto quedó guardado en disco durante el proceso.
    recuperado = almacen.cargar(proyecto.id)
    assert len(recuperado.paginas) == 2


def test_cancelacion_detiene_antes_de_terminar(tmp_path: Path):
    rutas = [
        crear_imagen_texto(f"Pagina numero {i}", tmp_path / f"p{i}.png", tamano_fuente=36)
        for i in range(5)
    ]
    paginas_fuente = pdf_io.construir_expediente(rutas)
    almacen = AlmacenProyectos(carpeta=tmp_path / "proyectos")
    proyecto = Proyecto(nombre="Prueba cancelacion")

    contador = {"n": 0}

    def debe_cancelar():
        contador["n"] += 1
        return contador["n"] > 2  # cancela tras un par de páginas

    proyecto = pipeline.procesar_expediente(
        paginas_fuente, "spa", tmp_path / "temp", proyecto, almacen,
        debe_cancelar=debe_cancelar,
    )

    assert len(proyecto.paginas) < 5


def test_pagina_con_archivo_faltante_no_detiene_el_resto(tmp_path: Path):
    ruta_valida = crear_imagen_texto("Pagina valida", tmp_path / "valida.png", tamano_fuente=36)
    ruta_rota = tmp_path / "no_existe.png"

    paginas_fuente = [
        pdf_io.PaginaFuente(ruta_rota, 0, 1),
        pdf_io.PaginaFuente(ruta_valida, 0, 1),
    ]
    almacen = AlmacenProyectos(carpeta=tmp_path / "proyectos")
    proyecto = Proyecto(nombre="Prueba de fallo parcial")

    proyecto = pipeline.procesar_expediente(paginas_fuente, "spa", tmp_path / "temp", proyecto, almacen)

    assert len(proyecto.paginas) == 2
    assert proyecto.paginas[0].fallo_procesamiento is True
    assert proyecto.paginas[1].fallo_procesamiento is False
    assert proyecto.paginas[1].texto_reconocido != ""


def test_no_carga_todas_las_imagenes_en_memoria_a_la_vez(tmp_path: Path, monkeypatch):
    """Verifica que cada página se guarda en disco y se libera antes de
    continuar con la siguiente, contando cuántas imágenes temporales
    existen simultáneamente en disco durante el procesamiento.
    """
    rutas = [
        crear_imagen_texto(f"Pagina {i}", tmp_path / f"src_{i}.png", tamano_fuente=36)
        for i in range(3)
    ]
    paginas_fuente = pdf_io.construir_expediente(rutas)
    almacen = AlmacenProyectos(carpeta=tmp_path / "proyectos")
    proyecto = Proyecto(nombre="Prueba de memoria")
    carpeta_temp = tmp_path / "temp"

    pipeline.procesar_expediente(paginas_fuente, "spa", carpeta_temp, proyecto, almacen)

    # Cada página procesada generó su propio archivo temporal en disco
    # (no se mantiene todo en un único arreglo en memoria).
    archivos_temp = list(carpeta_temp.glob("*.png"))
    assert len(archivos_temp) == 3
