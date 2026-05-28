"""
Selector de procesador por sección para RMDE.
"""

import re
from typing import Callable, Dict, Optional

from Modules.sections import articulos
from Modules.sections import analisis_regional
from Modules.sections import estudios_jurisprudenciales
from Modules.sections import notas_metodologicas
from Modules.sections import observatorio_electoral

CODIGO_ARTICULOS = "art"
CODIGOS_VALIDOS = {CODIGO_ARTICULOS, "nm", "ej", "ar", "oe"}

ProcesadorSeccion = Callable[[str, list, str, str], bool]

PROCESADORES: Dict[str, ProcesadorSeccion] = {
    CODIGO_ARTICULOS: articulos.procesar,
    "nm": notas_metodologicas.procesar,
    "ej": estudios_jurisprudenciales.procesar,
    "ar": analisis_regional.procesar,
    "oe": observatorio_electoral.procesar,
}


def extraer_codigo_seccion(nombre_carpeta: str) -> str:
    """Extrae el código de sección desde un nombre de carpeta RMDE.

    Ejemplos:
        20445_rmde-web-resources -> art
        20460_rmde_nm-web-resources -> nm
    """
    patron = r"^\d+_rmde(?:_([a-z]{2}))?(?:-web-resources)?$"
    match = re.match(patron, nombre_carpeta.strip(), flags=re.IGNORECASE)
    if not match:
        return CODIGO_ARTICULOS

    codigo = match.group(1)
    if not codigo:
        return CODIGO_ARTICULOS

    codigo = codigo.lower()
    if codigo in CODIGOS_VALIDOS:
        return codigo
    return CODIGO_ARTICULOS


def obtener_procesador_por_seccion(codigo_seccion: Optional[str]) -> ProcesadorSeccion:
    """Devuelve el procesador para la sección, con fallback a artículos."""
    if not codigo_seccion:
        return PROCESADORES[CODIGO_ARTICULOS]

    return PROCESADORES.get(codigo_seccion.lower(), PROCESADORES[CODIGO_ARTICULOS])
