from pathlib import Path

from transcriptor_notarial.core.project_store import (
    AlmacenProyectos, Proyecto, PaginaProyecto, PalabraProyecto,
)


def test_guardar_y_cargar_proyecto(tmp_path: Path):
    almacen = AlmacenProyectos(carpeta=tmp_path)
    proyecto = Proyecto(nombre="Expediente de prueba")
    proyecto.paginas.append(
        PaginaProyecto(
            numero=1,
            ruta_imagen_temporal="/tmp/pagina1.png",
            texto_reconocido="texto original",
            texto_corregido="texto corregido",
            palabras=[PalabraProyecto(texto="palabra", confianza=72.5, x=1, y=2, ancho=3, alto=4)],
        )
    )
    almacen.guardar(proyecto)

    recuperado = almacen.cargar(proyecto.id)
    assert recuperado.nombre == "Expediente de prueba"
    assert len(recuperado.paginas) == 1
    assert recuperado.paginas[0].texto_corregido == "texto corregido"
    assert recuperado.paginas[0].palabras[0].confianza == 72.5


def test_proyecto_no_cerrado_aparece_para_recuperacion(tmp_path: Path):
    almacen = AlmacenProyectos(carpeta=tmp_path)
    proyecto = Proyecto(nombre="Sesion interrumpida")
    almacen.guardar(proyecto)

    pendientes = almacen.listar_proyectos_sin_cerrar()
    assert any(p.id == proyecto.id for p in pendientes)


def test_proyecto_cerrado_no_aparece_para_recuperacion(tmp_path: Path):
    almacen = AlmacenProyectos(carpeta=tmp_path)
    proyecto = Proyecto(nombre="Sesion completa")
    almacen.marcar_cerrado_correctamente(proyecto)

    pendientes = almacen.listar_proyectos_sin_cerrar()
    assert not any(p.id == proyecto.id for p in pendientes)


def test_eliminar_proyecto(tmp_path: Path):
    almacen = AlmacenProyectos(carpeta=tmp_path)
    proyecto = Proyecto(nombre="Para borrar")
    almacen.guardar(proyecto)
    almacen.eliminar(proyecto.id)
    assert not (tmp_path / f"{proyecto.id}.json").exists()


def test_proyecto_no_guarda_rutas_de_imagen_duplicadas_como_binario(tmp_path: Path):
    """El proyecto solo guarda referencias (rutas), nunca el contenido de la
    imagen: el archivo JSON no debe contener bytes de imagen.
    """
    almacen = AlmacenProyectos(carpeta=tmp_path)
    proyecto = Proyecto(nombre="Revisión de tamaño")
    proyecto.paginas.append(
        PaginaProyecto(numero=1, ruta_imagen_temporal="/tmp/x.png", texto_reconocido="", texto_corregido="")
    )
    ruta = almacen.guardar(proyecto)
    assert ruta.stat().st_size < 5000
