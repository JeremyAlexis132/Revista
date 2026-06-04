"""
Módulo de utilidades específicas para la Revista Mexicana de Derecho Electoral (RMDE).
"""

import re
from typing import Optional

def es_carpeta_valida(nombre_carpeta: str) -> bool:
    """Filtra solo las carpetas que pertenecen a RMDE."""
    return "_rmde" in nombre_carpeta.lower()

def extraer_id_de_carpeta(nombre_carpeta: str) -> Optional[str]:
    match = re.match(r"^(\d+)", nombre_carpeta)
    return match.group(1) if match else None

def extraer_codigo_seccion(nombre_carpeta: str) -> str:
    patron = r"^\d+_rmde(?:_([a-z]{2}))?(?:-web-resources)?$"
    match = re.match(patron, nombre_carpeta.strip(), flags=re.IGNORECASE)
    if not match:
        return "art"

    codigo = match.group(1)
    if not codigo:
        return "art"

    codigo = codigo.lower()
    if codigo in {"nm", "ej", "ar", "oe"}:
        return codigo
    return "art"

def construir_clave_bitacora(nombre_carpeta: str) -> Optional[str]:
    revista_id = extraer_id_de_carpeta(nombre_carpeta)
    if revista_id is None:
        return None
    codigo = extraer_codigo_seccion(nombre_carpeta)
    return f"{revista_id}:{codigo}"