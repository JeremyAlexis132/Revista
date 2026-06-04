"""
Procesador de sección: artículos (sin subíndice).
"""

from typing import List

from Modules.core.sections.base import procesar_seccion_base


def procesar(
    html_path: str,
    css_inline: str,
    ruta_salida_html: str,
    nombre_revista: str,
) -> bool:
    return procesar_seccion_base(
        html_path=html_path,
        css_inline=css_inline,
        ruta_salida_html=ruta_salida_html,
        nombre_revista=nombre_revista,
        tipo_articulo_forzado="Artículo",
    )
