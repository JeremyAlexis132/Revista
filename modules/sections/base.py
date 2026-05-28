"""
Utilidades base para procesadores por sección de RMDE.
"""

from typing import List

from Modules.html_processor import procesar_html


def procesar_seccion_base(
    html_path: str,
    archivos_css: List[str],
    ruta_salida_html: str,
    nombre_revista: str,
    tipo_articulo_forzado: str = "",
) -> bool:
    """Procesa el HTML de una sección usando el flujo estándar actual."""
    return procesar_html(
        html_path=html_path,
        archivos_css=archivos_css,
        ruta_salida_html=ruta_salida_html,
        nombre_revista=nombre_revista,
        tipo_articulo_forzado=tipo_articulo_forzado,
    )
