"""
Módulo de utilidades específicas para el Boletín Mexicano de Derecho Comparado (BMDC).
"""

import re
from typing import Optional

def es_carpeta_valida(nombre_carpeta: str) -> bool:
    """Filtra solo las carpetas que pertenecen a BMDC."""
    return "_bmdc" in nombre_carpeta.lower()

def extraer_id_de_carpeta(nombre_carpeta: str) -> Optional[str]:
    match = re.match(r"^(\d+)", nombre_carpeta)
    return match.group(1) if match else None

def extraer_codigo_seccion(nombre_carpeta: str) -> str:
    return "art"

def construir_clave_bitacora(nombre_carpeta: str) -> Optional[str]:
    revista_id = extraer_id_de_carpeta(nombre_carpeta)
    if revista_id is None:
        return None
    return f"{revista_id}:bmdc"