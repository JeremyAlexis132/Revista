"""
Utilidades base para procesadores por sección de RMDE.
"""

from typing import List
from Modules.journals.rmde.html_processor import procesar_html

def procesar_seccion_base(
    html_path: str,
    css_inline: str, 
    ruta_salida_html: str,
    nombre_revista: str,
    tipo_articulo_forzado: str = "",
) -> bool:
    """Procesa el HTML de una sección usando el flujo estándar actual."""
    return procesar_html(
        html_path=html_path,
        css_inline=css_inline,
        ruta_salida_html=ruta_salida_html,
        nombre_revista=nombre_revista,
        tipo_articulo_forzado=tipo_articulo_forzado,
    )