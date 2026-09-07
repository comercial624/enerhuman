"""Detección de elementos relevantes en actas notariales mediante reglas y
expresiones regulares locales.

Importante: este módulo SOLO detecta y señala. Nunca modifica, corrige ni
reescribe el texto reconocido. Toda corrección la hace el usuario.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class TipoEntidad(str, Enum):
    NOMBRE_COMPLETO = "nombre_completo"
    FECHA = "fecha"
    CANTIDAD_NUMERO = "cantidad_numero"
    CANTIDAD_LETRA = "cantidad_letra"
    NUMERO_ESCRITURA = "numero_escritura"
    NUMERO_INSTRUMENTO = "numero_instrumento"
    FOLIO = "folio"
    EXPEDIENTE = "expediente"
    DOMICILIO = "domicilio"
    CODIGO_POSTAL = "codigo_postal"
    CLAVE_CATASTRAL = "clave_catastral"
    DATO_REGISTRAL = "dato_registral"
    SUPERFICIE = "superficie"
    MEDIDA = "medida"
    COLINDANCIA = "colindancia"
    PORCENTAJE = "porcentaje"
    MONEDA = "moneda"
    IDENTIFICACION = "identificacion"
    CORREO = "correo"
    ALFANUMERICO_INUSUAL = "alfanumerico_inusual"


@dataclass
class Coincidencia:
    tipo: TipoEntidad
    texto: str
    inicio: int
    fin: int

    def a_diccionario(self) -> dict:
        return {
            "tipo": self.tipo.value,
            "texto": self.texto,
            "inicio": self.inicio,
            "fin": self.fin,
        }


MESES = (
    "enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|"
    "octubre|noviembre|diciembre"
)

# El orden importa: patrones más específicos primero para que, al filtrar
# solapamientos, gane el más informativo (p. ej. "número de escritura" antes
# que un genérico "alfanumérico inusual").
_PATRONES: list[tuple[TipoEntidad, re.Pattern]] = [
    (
        TipoEntidad.CORREO,
        re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", re.UNICODE),
    ),
    (
        TipoEntidad.CODIGO_POSTAL,
        re.compile(r"\bC\.?\s?P\.?\s*[:\-]?\s*\d{5}\b", re.IGNORECASE),
    ),
    (
        TipoEntidad.NUMERO_ESCRITURA,
        re.compile(
            r"\b(?:escritura|instrumento)\s+(?:p[uú]blic[oa]\s+)?(?:n[uú]mero|no\.?|n[o°º]\.?)\s*[:\-]?\s*\d{1,7}\b",
            re.IGNORECASE,
        ),
    ),
    (
        TipoEntidad.NUMERO_INSTRUMENTO,
        re.compile(
            r"\b(?:volumen|vol\.?)\s*\d{1,6}\b[,\s]*"
            r"(?:foja|fojas)?\s*\d{0,6}",
            re.IGNORECASE,
        ),
    ),
    (
        TipoEntidad.FOLIO,
        re.compile(
            r"\b(?:folio|foja|fojas)\s+(?:real\s+)?(?:mercantil\s+)?(?:electr[oó]nic[oa]\s+)?(?:n[uú]mero\s+)?\d{1,10}(?:-\d{1,4})?\b",
            re.IGNORECASE,
        ),
    ),
    (
        TipoEntidad.EXPEDIENTE,
        re.compile(
            r"\bexpediente\s*(?:n[uú]mero|no\.?)?\s*[:\-]?\s*[A-Z0-9\-/]{3,20}\b",
            re.IGNORECASE,
        ),
    ),
    (
        TipoEntidad.CLAVE_CATASTRAL,
        re.compile(
            r"\bclave\s+catastral\s*[:\-]?\s*[0-9]{2,4}(?:[- ][0-9A-Z]{2,6}){2,8}\b",
            re.IGNORECASE,
        ),
    ),
    (
        TipoEntidad.DATO_REGISTRAL,
        re.compile(
            r"\b(?:Registro\s+P[uú]blico\s+de\s+la\s+Propiedad|inscripci[oó]n)\b[^.\n]{0,80}",
            re.IGNORECASE,
        ),
    ),
    (
        TipoEntidad.SUPERFICIE,
        re.compile(
            r"\b\d{1,3}(?:[.,]\d{1,4})?\s*(?:m2|m²|metros\s+cuadrados|hect[aá]reas|ha\b)",
            re.IGNORECASE,
        ),
    ),
    (
        TipoEntidad.MEDIDA,
        re.compile(
            r"\b\d{1,4}(?:[.,]\d{1,4})?\s*(?:metros|mts?\.?|cent[ií]metros|cm\b|km\b)\b",
            re.IGNORECASE,
        ),
    ),
    (
        TipoEntidad.COLINDANCIA,
        re.compile(
            r"\b(?:al\s+(?:norte|sur|este|oeste|noreste|noroeste|sureste|suroeste)|colinda(?:\s+con)?)\b[^.\n]{0,100}",
            re.IGNORECASE,
        ),
    ),
    (
        TipoEntidad.PORCENTAJE,
        re.compile(r"\b\d{1,3}(?:[.,]\d{1,2})?\s?%|\b\d{1,3}(?:[.,]\d{1,2})?\s+por\s+ciento\b", re.IGNORECASE),
    ),
    (
        TipoEntidad.MONEDA,
        re.compile(
            r"\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(?:pesos|M\.?N\.?|USD|d[oó]lares)\b",
            re.IGNORECASE,
        ),
    ),
    (
        TipoEntidad.CANTIDAD_LETRA,
        re.compile(
            r"\b(?:un|una|uno|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|"
            r"once|doce|trece|catorce|quince|veinte|treinta|cuarenta|cincuenta|"
            r"sesenta|setenta|ochenta|noventa|cien|ciento|doscientos|trescientos|"
            r"cuatrocientos|quinientos|seiscientos|setecientos|ochocientos|"
            r"novecientos|mil|mill[oó]n|millones)\b"
            r"(?:\s+(?:y|de|mil|cientos?|[a-zá-úñ]+)){0,6}"
            r"(?:\s+pesos|\s+d[oó]lares)?\b",
            re.IGNORECASE,
        ),
    ),
    (
        TipoEntidad.FECHA,
        re.compile(
            rf"\b\d{{1,2}}\s+de\s+(?:{MESES})\s+de\s+(?:mil\s+[a-zá-úñ\s]+|\d{{4}})\b"
            rf"|\b\d{{1,2}}[/\-]\d{{1,2}}[/\-]\d{{2,4}}\b",
            re.IGNORECASE,
        ),
    ),
    (
        TipoEntidad.DOMICILIO,
        re.compile(
            r"\b(?:calle|avenida|av\.?|boulevard|blvd\.?|privada|andador|carretera|"
            r"prolongaci[oó]n)\s+[A-Za-zÁÉÍÓÚÑáéíóúñ0-9.\s]{3,60}?(?:,|\bn[uú]mero\b|\bno\.?\b|\d+)",
            re.IGNORECASE,
        ),
    ),
    (
        TipoEntidad.IDENTIFICACION,
        re.compile(
            r"\b(?:CURP|RFC|INE|IFE)\s*[:\-]?\s*[A-Z0-9]{6,18}\b",
            re.IGNORECASE,
        ),
    ),
    (
        TipoEntidad.NOMBRE_COMPLETO,
        re.compile(
            r"\b(?:[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+){1,3}[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+"
            r"[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\b"
        ),
    ),
    (
        TipoEntidad.ALFANUMERICO_INUSUAL,
        re.compile(r"\b(?=[A-Za-z0-9]{5,20}\b)(?=[A-Za-z0-9]*[0-9])(?=[A-Za-z0-9]*[A-Za-z])[A-Za-z0-9]{5,20}\b"),
    ),
]


def detectar_entidades(texto: str) -> list[Coincidencia]:
    """Devuelve todas las coincidencias encontradas en `texto`.

    Se eliminan solapamientos: si dos patrones cubren el mismo tramo de
    texto, se conserva el de mayor prioridad (el que aparece antes en
    `_PATRONES`) y se descarta el resto para no duplicar resaltados.
    """
    encontradas: list[Coincidencia] = []
    rangos_ocupados: list[tuple[int, int]] = []

    for tipo, patron in _PATRONES:
        for m in patron.finditer(texto):
            inicio, fin = m.start(), m.end()
            if any(not (fin <= r0 or inicio >= r1) for r0, r1 in rangos_ocupados):
                continue
            encontradas.append(Coincidencia(tipo, m.group(0), inicio, fin))
            rangos_ocupados.append((inicio, fin))

    encontradas.sort(key=lambda c: c.inicio)
    return encontradas


_PATRON_NUMERO = re.compile(r"\b\d[\d,]*(?:\.\d+)?\b")
_PATRON_LETRA_NUMERICA = re.compile(
    r"\b(?:un|una|uno|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|"
    r"once|doce|trece|catorce|quince|veinte|treinta|cuarenta|cincuenta|"
    r"sesenta|setenta|ochenta|noventa|cien|ciento|mil|mill[oó]n|millones)\b",
    re.IGNORECASE,
)


def verificar_consistencia_cantidades(texto: str) -> list[str]:
    """Compara cantidades en número y en letra dentro del mismo texto.

    No corrige nada: solo devuelve advertencias en español para que el
    empleado compruebe manualmente ambas versiones cuando el texto contiene
    tanto una expresión numérica como una expresión en letra que podrían
    corresponder a la misma cantidad (p. ej. "$50,000.00 (cincuenta mil
    pesos 00/100 M.N.)").
    """
    advertencias: list[str] = []
    tiene_numero = bool(_PATRON_NUMERO.search(texto))
    tiene_letra = bool(_PATRON_LETRA_NUMERICA.search(texto))
    if tiene_numero and tiene_letra:
        advertencias.append(
            "Se detectó una cantidad expresada con número y otra con letra: "
            "verifique que ambas coincidan exactamente."
        )
    return advertencias
