#!/usr/bin/env python3
"""Genera un listado de archivos con tamaños y el hash SHA-256 de la
carpeta portátil (y, si existe, del ZIP y el .exe sueltos), como evidencia
de integridad para distribuir junto con la entrega.

Uso:
    python packaging\\generate_hashes.py dist\\Transcriptor_Notarial_Portable
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path


def sha256_de_archivo(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloque)
    return h.hexdigest()


def generar_listado(carpeta: Path, ruta_salida: Path) -> None:
    archivos = sorted(p for p in carpeta.rglob("*") if p.is_file())
    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write(f"Listado de archivos y hashes SHA-256 — {carpeta.name}\n")
        f.write("=" * 70 + "\n\n")
        for archivo in archivos:
            tamano = archivo.stat().st_size
            hash_archivo = sha256_de_archivo(archivo)
            ruta_relativa = archivo.relative_to(carpeta)
            f.write(f"{hash_archivo}  {tamano:>12} bytes  {ruta_relativa}\n")
    print(f"Listado generado en: {ruta_salida}")


def main() -> int:
    if len(sys.argv) < 2:
        print("Uso: python generate_hashes.py <carpeta_portable> [archivo.zip] [archivo.exe]")
        return 1

    carpeta = Path(sys.argv[1])
    if not carpeta.exists():
        print(f"No existe la carpeta: {carpeta}")
        return 1

    ruta_listado = carpeta.parent / f"{carpeta.name}_hashes_sha256.txt"
    generar_listado(carpeta, ruta_listado)

    for extra in sys.argv[2:]:
        ruta_extra = Path(extra)
        if ruta_extra.exists():
            hash_extra = sha256_de_archivo(ruta_extra)
            print(f"SHA-256 de {ruta_extra.name}: {hash_extra}")
            with open(ruta_listado, "a", encoding="utf-8") as f:
                f.write(f"\n{hash_extra}  {ruta_extra.stat().st_size:>12} bytes  {ruta_extra.name} (fuera de la carpeta)\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
