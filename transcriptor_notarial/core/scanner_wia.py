"""Escaneo directo mediante WIA (Windows Image Acquisition), solo Windows.

Módulo independiente y opcional: si no hay escáner, si no hay controladores
compatibles o si el sistema no es Windows, la aplicación sigue funcionando
normalmente mediante selección de archivos PDF/imágenes. Ninguna otra parte
del programa depende de que este módulo funcione.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_WIA_DISPONIBLE = False
if os.name == "nt":
    try:
        import win32com.client  # type: ignore
        import pythoncom  # type: ignore
        _WIA_DISPONIBLE = True
    except ImportError:
        _WIA_DISPONIBLE = False

WIA_FORMATO_PNG = "{B96B3CAE-0728-11D3-9D7B-0000F81EF32E}"

# Constantes del modelo de propiedades WIA para el elemento de imagen.
WIA_PROP_HORIZONTAL_RES = 6147
WIA_PROP_VERTICAL_RES = 6148
WIA_PROP_COLOR_INTENT = 6146  # 1=color, 2=escala de grises, 4=blanco y negro


class EscanerNoDisponibleError(Exception):
    pass


@dataclass
class DispositivoEscaner:
    id_dispositivo: str
    nombre: str


def wia_disponible() -> bool:
    return _WIA_DISPONIBLE


def listar_escaneres() -> list[DispositivoEscaner]:
    """Enumera los escáneres WIA disponibles. Devuelve lista vacía (nunca
    lanza excepción) si WIA no está disponible o no hay dispositivos.
    """
    if not _WIA_DISPONIBLE:
        return []
    try:
        pythoncom.CoInitialize()
        try:
            gestor = win32com.client.Dispatch("WIA.DeviceManager")
            dispositivos = []
            for info in gestor.DeviceInfos:
                if info.Type == 1:  # 1 = StiDeviceTypeScanner
                    dispositivos.append(
                        DispositivoEscaner(id_dispositivo=info.DeviceID, nombre=str(info.Properties("Name")))
                    )
            return dispositivos
        finally:
            pythoncom.CoUninitialize()
    except Exception:
        return []


def escanear_pagina(
    id_dispositivo: str | None,
    ruta_salida: Path,
    dpi: int = 300,
    color: bool = True,
) -> Path:
    """Escanea una página y la guarda como PNG en `ruta_salida`.

    Si `id_dispositivo` es None, se usa el primer escáner disponible.
    Lanza EscanerNoDisponibleError si WIA no está disponible, no hay
    dispositivos o falla la comunicación con el escáner/controlador.
    """
    if not _WIA_DISPONIBLE:
        raise EscanerNoDisponibleError(
            "El escaneo directo solo está disponible en Windows con WIA."
        )

    pythoncom.CoInitialize()
    try:
        gestor = win32com.client.Dispatch("WIA.DeviceManager")
        dispositivos = list(gestor.DeviceInfos)
        if not dispositivos:
            raise EscanerNoDisponibleError("No se detectó ningún escáner conectado.")

        info_elegida = None
        for info in dispositivos:
            if info.Type == 1 and (id_dispositivo is None or info.DeviceID == id_dispositivo):
                info_elegida = info
                break
        if info_elegida is None:
            raise EscanerNoDisponibleError("No se encontró el escáner solicitado.")

        try:
            dispositivo = info_elegida.Connect()
        except Exception as e:
            raise EscanerNoDisponibleError(
                "No se pudo conectar con el escáner. Verifique que esté "
                "encendido, conectado y que el controlador esté instalado."
            ) from e

        item = dispositivo.Items[0]
        try:
            item.Properties(WIA_PROP_HORIZONTAL_RES).Value = dpi
            item.Properties(WIA_PROP_VERTICAL_RES).Value = dpi
            item.Properties(WIA_PROP_COLOR_INTENT).Value = 1 if color else 2
        except Exception:
            # Algunos controladores no exponen todas las propiedades;
            # se continúa con los valores predeterminados del dispositivo.
            pass

        imagen = item.Transfer(WIA_FORMATO_PNG)
        ruta_salida = Path(ruta_salida)
        ruta_salida.parent.mkdir(parents=True, exist_ok=True)
        if ruta_salida.exists():
            ruta_salida.unlink()
        imagen.SaveFile(str(ruta_salida))
        return ruta_salida
    finally:
        pythoncom.CoUninitialize()
