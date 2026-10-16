"""
Módulo de utilidades específicas para la revista Problema.
Anuario de Filosofía y Teoría del Derecho (módulo p).

Las operaciones genéricas (bitácora, copiar imágenes, buscar HTML/CSS, crear
carpeta de salida) viven en Modules/core/utils_base.py y se comparten con el
resto de las revistas.
"""

import re
from typing import Optional

NOMBRE_REVISTA = "Problema. Anuario de Filosofía y Teoría del Derecho"
CODIGO_REVISTA = "p"
MARCA_CARPETA = "_problema"


def es_carpeta_valida(nombre_carpeta: str) -> bool:
    """Filtra solo las carpetas que pertenecen a Problema (p. ej. 18534_mendoza_problema)."""
    return MARCA_CARPETA in nombre_carpeta.lower()


def extraer_id_de_carpeta(nombre_carpeta: str) -> Optional[str]:
    match = re.match(r"^(\d+)", nombre_carpeta)
    return match.group(1) if match else None


def extraer_codigo_seccion(nombre_carpeta: str) -> str:
    """
    Problema no distingue secciones en el nombre de la carpeta: todo es "art".
    Si más adelante se agregan sufijos (p. ej. 18534_mendoza_problema_ej),
    basta con ampliar este patrón y el conjunto de códigos válidos.
    """
    patron = r"^\d+_[a-z0-9\-]+_problema(?:_([a-z]{2}))?(?:-web-resources)?$"
    match = re.match(patron, nombre_carpeta.strip(), flags=re.IGNORECASE)
    if not match or not match.group(1):
        return "art"
    codigo = match.group(1).lower()
    return codigo if codigo in set() else "art"


def construir_clave_bitacora(nombre_carpeta: str) -> Optional[str]:
    revista_id = extraer_id_de_carpeta(nombre_carpeta)
    if revista_id is None:
        return None
    return f"{revista_id}:{extraer_codigo_seccion(nombre_carpeta)}"
