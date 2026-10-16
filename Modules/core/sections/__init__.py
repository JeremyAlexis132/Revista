"""
Módulo central para la gestión y enrutamiento de secciones de revistas.
Identifica el tipo de artículo dinámicamente escaneando la ruta completa del archivo y la carpeta.

Para dar de alta una revista nueva basta con agregarla al diccionario _REVISTAS.
"""

import importlib
import os
import re
from typing import Callable

# Mapeo universal de abreviaturas (fronteras de palabra \b para evitar falsos positivos)
_TITULOS_COMUNES = {
    r'\bcj\b': "Comentario jurisprudencial",
    r'\bcl\b': "Comentario legislativo",
    r'\brb\b': "Reseña bibliográfica",
    r'\bnm\b': "Nota metodológica",
    r'\bej\b': "Estudio jurisprudencial",
    r'\bar\b': "Análisis de reformas electorales",
    r'\boe\b': "Observatorio electoral",
    r'\bart\b': "Artículo",
}

# revista -> (módulo del html_processor, ¿la revista etiqueta el tipo de artículo?)
#   True : se detecta el tipo (Artículo, Reseña bibliográfica...) y se envía como
#          tipo_articulo_forzado, que el procesador imprime como etiqueta.
#   False: el procesador no usa etiqueta de tipo (Problema solo publica artículos
#          y su formato no lleva la etiqueta "Artículo" arriba del título).
_REVISTAS = {
    "rmde": ("Modules.journals.rmde.html_processor", True),
    "cc":   ("Modules.journals.cc.html_processor", True),
    "bmdc": ("Modules.journals.bmdc.html_processor", True),
    "rmdh": ("Modules.journals.rmdh.html_processor", True),
    "p":    ("Modules.journals.p.html_processor", False),
}


def _detectar_tipo(cadena: str) -> str:
    """Busca patrones de abreviaturas en una cadena normalizada."""
    # Convierte guiones bajos y normales en espacios para aislar la abreviatura
    cadena_limpia = cadena.lower().replace('_', ' ').replace('-', ' ')
    for patron, titulo in _TITULOS_COMUNES.items():
        if re.search(patron, cadena_limpia):
            return titulo
    return "Artículo"  # Valor por defecto seguro


def obtener_procesador_por_seccion(revista: str, codigo_seccion: str) -> Callable:
    if revista not in _REVISTAS:
        raise ValueError(f"La revista '{revista}' no está soportada.")

    ruta_modulo, etiqueta_tipo = _REVISTAS[revista]
    procesar = importlib.import_module(ruta_modulo).procesar_html

    if not etiqueta_tipo:
        return procesar

    def procesador_wrapper(**kwargs):
        ruta = kwargs.get("html_path", "")
        carpeta = os.path.basename(os.path.dirname(ruta)) if ruta else ""
        archivo = os.path.basename(ruta) if ruta else ""
        # Escanea la carpeta, el archivo y el código enviado por si acaso
        contexto_busqueda = f"{carpeta} {archivo} {codigo_seccion}"
        kwargs["tipo_articulo_forzado"] = _detectar_tipo(contexto_busqueda)
        return procesar(**kwargs)

    return procesador_wrapper