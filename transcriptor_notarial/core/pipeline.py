"""Orquestación del procesamiento de un expediente completo.

Pensado para ejecutarse dentro de un hilo de trabajo (QThread en la GUI) y
reportar progreso incremental sin cargar todas las imágenes de alta
resolución en memoria a la vez: cada página se procesa, se guarda su imagen
temporal en disco y se libera de memoria antes de continuar con la
siguiente.

Si falla una página, se registra el error y se continúa con las demás
(no se detiene todo el expediente por un problema puntual).
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

import cv2

from . import image_prep, ocr_engine, pdf_io, entities
from .project_store import PaginaProyecto, PalabraProyecto, Proyecto, AlmacenProyectos
from .. import paths, logging_setup


class EstadoProcesamiento(str, Enum):
    PREPARANDO_IMAGEN = "preparando_imagen"
    RECONOCIENDO_TEXTO = "reconociendo_texto"
    CREANDO_WORD = "creando_word"
    FINALIZADO = "finalizado"
    CANCELADO = "cancelado"


@dataclass
class ProgresoPagina:
    pagina_actual: int
    total_paginas: int
    porcentaje: float
    estado: EstadoProcesamiento
    tiempo_restante_estimado_s: Optional[float] = None
    etiqueta_pagina: str = ""


class ProcesamientoCancelado(Exception):
    pass


CallbackProgreso = Callable[[ProgresoPagina], None]
FuncionDebeCancelar = Callable[[], bool]


def _guardar_imagen_temporal(imagen_gris, carpeta_temporal: Path, num_pagina: int) -> Path:
    carpeta_temporal.mkdir(parents=True, exist_ok=True)
    ruta = carpeta_temporal / f"pagina_{num_pagina:04d}_{uuid.uuid4().hex[:8]}.png"
    cv2.imwrite(str(ruta), imagen_gris)
    return ruta


def procesar_expediente(
    paginas_fuente: list[pdf_io.PaginaFuente],
    idioma_ocr: str,
    carpeta_temporal: Path,
    proyecto: Proyecto,
    almacen: AlmacenProyectos,
    callback_progreso: Optional[CallbackProgreso] = None,
    debe_cancelar: Optional[FuncionDebeCancelar] = None,
    guardar_cada_n_paginas: int = 1,
) -> Proyecto:
    """Procesa todas las páginas del expediente y va llenando `proyecto`.

    Guarda el proyecto periódicamente (cada `guardar_cada_n_paginas`
    páginas) para poder recuperar la sesión si la aplicación se cierra de
    forma inesperada.
    """
    total = len(paginas_fuente)
    tiempos_por_pagina: list[float] = []
    inicio_total = time.monotonic()

    for indice, pagina_fuente in enumerate(paginas_fuente):
        num_pagina = indice + 1

        if debe_cancelar and debe_cancelar():
            if callback_progreso:
                callback_progreso(
                    ProgresoPagina(num_pagina, total, (indice / total) * 100 if total else 0,
                                    EstadoProcesamiento.CANCELADO)
                )
            almacen.guardar(proyecto)
            return proyecto

        inicio_pagina = time.monotonic()
        etiqueta = pagina_fuente.etiqueta

        try:
            if callback_progreso:
                callback_progreso(ProgresoPagina(
                    num_pagina, total, (indice / total) * 100 if total else 0,
                    EstadoProcesamiento.PREPARANDO_IMAGEN, etiqueta_pagina=etiqueta,
                ))

            texto_existente = pdf_io.extraer_texto_existente(pagina_fuente)
            imagen_bgr, dpi_estimado = pdf_io.rasterizar_pagina(pagina_fuente)
            resultados_prep = image_prep.preparar_imagen(imagen_bgr, dpi_estimado=dpi_estimado)

            for sub_resultado in resultados_prep:
                ruta_temporal = _guardar_imagen_temporal(sub_resultado.imagen, carpeta_temporal, num_pagina)

                palabras_proyecto: list[PalabraProyecto] = []
                if texto_existente and len(resultados_prep) == 1:
                    # El PDF ya trae una capa de texto: se usa directamente,
                    # es más confiable que el OCR y evita reinterpretar el
                    # documento.
                    texto_reconocido = texto_existente
                else:
                    if callback_progreso:
                        callback_progreso(ProgresoPagina(
                            num_pagina, total, (indice / total) * 100 if total else 0,
                            EstadoProcesamiento.RECONOCIENDO_TEXTO, etiqueta_pagina=etiqueta,
                        ))
                    resultado_ocr = ocr_engine.reconocer_pagina(
                        sub_resultado.imagen, idioma=idioma_ocr, num_pagina=num_pagina
                    )
                    texto_reconocido = resultado_ocr.texto_completo
                    palabras_proyecto = [
                        PalabraProyecto(
                            texto=p.texto, confianza=p.confianza,
                            x=p.x, y=p.y, ancho=p.ancho, alto=p.alto,
                        )
                        for p in resultado_ocr.palabras
                    ]

                pagina_proyecto = PaginaProyecto(
                    numero=num_pagina,
                    ruta_imagen_temporal=str(ruta_temporal),
                    texto_reconocido=texto_reconocido,
                    texto_corregido=texto_reconocido,
                    palabras=palabras_proyecto,
                )
                proyecto.paginas.append(pagina_proyecto)

            duracion_pagina = time.monotonic() - inicio_pagina
            tiempos_por_pagina.append(duracion_pagina)

        except Exception as e:
            pagina_proyecto = PaginaProyecto(
                numero=num_pagina,
                ruta_imagen_temporal="",
                texto_reconocido="",
                texto_corregido="",
                fallo_procesamiento=True,
                mensaje_error=type(e).__name__,
            )
            proyecto.paginas.append(pagina_proyecto)
            logging_setup.registrar_evento(
                "procesar_pagina", num_paginas=1, tipo_error=type(e).__name__
            )

        if (indice + 1) % guardar_cada_n_paginas == 0:
            almacen.guardar(proyecto)

        promedio = sum(tiempos_por_pagina) / len(tiempos_por_pagina) if tiempos_por_pagina else None
        restante = promedio * (total - num_pagina) if promedio else None

        if callback_progreso:
            callback_progreso(ProgresoPagina(
                num_pagina, total, (num_pagina / total) * 100 if total else 100,
                EstadoProcesamiento.RECONOCIENDO_TEXTO, tiempo_restante_estimado_s=restante,
                etiqueta_pagina=etiqueta,
            ))

    almacen.guardar(proyecto)
    duracion_total = time.monotonic() - inicio_total
    logging_setup.registrar_evento(
        "procesar_documento", duracion_segundos=duracion_total, num_paginas=total
    )

    if callback_progreso:
        callback_progreso(ProgresoPagina(total, total, 100.0, EstadoProcesamiento.FINALIZADO))

    return proyecto
