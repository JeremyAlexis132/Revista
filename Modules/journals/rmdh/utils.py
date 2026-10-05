"""Utilidades de la Revista Mexicana de Historia del Derecho (RMDH)."""

import re
from typing import Optional


def es_carpeta_valida(nombre_carpeta: str) -> bool:
    return "_rmhd" in nombre_carpeta.lower()


def extraer_id_de_carpeta(nombre_carpeta: str) -> Optional[str]:
    match = re.match(r"^(\d+)", nombre_carpeta)
    return match.group(1) if match else None


def extraer_codigo_seccion(nombre_carpeta: str) -> str:
    patron = r"^\d+_rmhd(?:_([a-z]{2}))?(?:-web-resources)?$"
    match = re.match(patron, nombre_carpeta.strip(), flags=re.IGNORECASE)
    if not match or not match.group(1):
        return "art"
    codigo = match.group(1).lower()
    return codigo if codigo in {"cj", "cl", "rb", "nm", "ej", "ar", "oe"} else "art"


def construir_clave_bitacora(nombre_carpeta: str) -> Optional[str]:
    revista_id = extraer_id_de_carpeta(nombre_carpeta)
    if revista_id is None:
        return None
    return f"{revista_id}:{extraer_codigo_seccion(nombre_carpeta)}"