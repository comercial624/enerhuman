"""Persistencia de proyectos de revisión (expedientes en curso).

Un "proyecto" guarda, por cada página: el texto reconocido, las
correcciones del usuario, las coordenadas de las palabras y el estado de
revisión (revisada / pendiente). Se guarda en JSON dentro de una carpeta
local del usuario (nunca en la memoria USB por defecto), para poder
recuperar la sesión si la aplicación se cierra inesperadamente.

No se guarda ninguna imagen dentro del proyecto: solo una referencia a la
ruta temporal o de origen, para no duplicar contenido confidencial.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

from .. import paths


@dataclass
class PalabraProyecto:
    texto: str
    confianza: float
    x: int
    y: int
    ancho: int
    alto: int
    revisada: bool = False


@dataclass
class PaginaProyecto:
    numero: int
    ruta_imagen_temporal: str
    texto_reconocido: str
    texto_corregido: str
    palabras: list[PalabraProyecto] = field(default_factory=list)
    rotacion_grados: int = 0
    revisada: bool = False
    fallo_procesamiento: bool = False
    mensaje_error: str | None = None


@dataclass
class Proyecto:
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    nombre: str = "Expediente sin título"
    creado_en: str = field(default_factory=lambda: datetime.now().isoformat())
    modificado_en: str = field(default_factory=lambda: datetime.now().isoformat())
    archivos_origen: list[str] = field(default_factory=list)
    paginas: list[PaginaProyecto] = field(default_factory=list)
    idioma_ocr: str = "spa"
    cerrado_correctamente: bool = False

    def a_diccionario(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "creado_en": self.creado_en,
            "modificado_en": self.modificado_en,
            "archivos_origen": self.archivos_origen,
            "idioma_ocr": self.idioma_ocr,
            "cerrado_correctamente": self.cerrado_correctamente,
            "paginas": [
                {
                    **asdict(p),
                    "palabras": [asdict(w) for w in p.palabras],
                }
                for p in self.paginas
            ],
        }

    @staticmethod
    def desde_diccionario(datos: dict) -> "Proyecto":
        paginas = []
        for pd in datos.get("paginas", []):
            palabras = [PalabraProyecto(**w) for w in pd.get("palabras", [])]
            pd2 = {k: v for k, v in pd.items() if k != "palabras"}
            paginas.append(PaginaProyecto(**pd2, palabras=palabras))
        return Proyecto(
            id=datos.get("id", uuid.uuid4().hex),
            nombre=datos.get("nombre", "Expediente sin título"),
            creado_en=datos.get("creado_en", datetime.now().isoformat()),
            modificado_en=datos.get("modificado_en", datetime.now().isoformat()),
            archivos_origen=datos.get("archivos_origen", []),
            idioma_ocr=datos.get("idioma_ocr", "spa"),
            cerrado_correctamente=datos.get("cerrado_correctamente", False),
            paginas=paginas,
        )


class AlmacenProyectos:
    def __init__(self, carpeta: Path | None = None):
        self.carpeta = carpeta or paths.projects_dir()
        self.carpeta.mkdir(parents=True, exist_ok=True)

    def _ruta(self, id_proyecto: str) -> Path:
        return self.carpeta / f"{id_proyecto}.json"

    def guardar(self, proyecto: Proyecto) -> Path:
        proyecto.modificado_en = datetime.now().isoformat()
        ruta = self._ruta(proyecto.id)
        tmp = ruta.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(proyecto.a_diccionario(), f, ensure_ascii=False, indent=2)
        tmp.replace(ruta)
        return ruta

    def cargar(self, id_proyecto: str) -> Proyecto:
        ruta = self._ruta(id_proyecto)
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)
        return Proyecto.desde_diccionario(datos)

    def listar_proyectos_sin_cerrar(self) -> list[Proyecto]:
        """Proyectos que no se cerraron correctamente: candidatos para
        ofrecer recuperación de sesión al iniciar la aplicación.
        """
        pendientes = []
        for archivo in self.carpeta.glob("*.json"):
            try:
                with open(archivo, "r", encoding="utf-8") as f:
                    datos = json.load(f)
                if not datos.get("cerrado_correctamente", False):
                    pendientes.append(Proyecto.desde_diccionario(datos))
            except (json.JSONDecodeError, OSError):
                continue
        return pendientes

    def eliminar(self, id_proyecto: str) -> None:
        ruta = self._ruta(id_proyecto)
        if ruta.exists():
            ruta.unlink()

    def marcar_cerrado_correctamente(self, proyecto: Proyecto) -> None:
        proyecto.cerrado_correctamente = True
        self.guardar(proyecto)
