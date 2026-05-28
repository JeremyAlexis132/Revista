"""
Procesador de sección: artículos (sin subíndice).
"""

from typing import List

from Modules.sections.base import procesar_seccion_base


def procesar(
    html_path: str,
    archivos_css: List[str],
    ruta_salida_html: str,
    nombre_revista: str,
) -> bool:
    return procesar_seccion_base(
        html_path=html_path,
        archivos_css=archivos_css,
        ruta_salida_html=ruta_salida_html,
        nombre_revista=nombre_revista,
        tipo_articulo_forzado="Artículo",
    )
