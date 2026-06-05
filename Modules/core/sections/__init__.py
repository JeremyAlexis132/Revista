"""
Módulo central para la gestión y enrutamiento de secciones de revistas.
Identifica el tipo de artículo dinámicamente a partir del nombre de la carpeta,
buscando coincidencias exactas con las abreviaturas definidas.
"""

import re
from typing import Callable

def obtener_procesador_por_seccion(revista: str, codigo_seccion: str) -> Callable:
    """
    Fábrica que devuelve la función procesadora adecuada según la revista y el código de sección.
    """
    # 1. Tokenizamos el nombre de la carpeta separando por guiones, guiones bajos o espacios
    codigo_limpio = codigo_seccion.lower().strip()
    tokens = re.split(r'[_ \-]', codigo_limpio)
    
    # 2. Mapeo universal de abreviaturas
    titulos_comunes = {
        "cj": "Comentario jurisprudencial",
        "cl": "Comentario legislativo",
        "rb": "Reseña bibliográfica",
        "nm": "Nota metodológica",
        "ej": "Estudio jurisprudencial",
        "ar": "Análisis regional",
        "oe": "Observatorio electoral",
        "art": "Artículo",
        "web": "Artículo"
    }

    # Valor por defecto
    tipo_articulo = "Artículo"

    # 3. Buscamos si alguna de las abreviaturas está como token independiente
    for token in tokens:
        # Quitamos terminaciones 'web' si quedaron pegadas (ej. 'cjweb' -> 'cj')
        token_base = token.replace("web", "").replace("resources", "")
        if token in titulos_comunes:
            tipo_articulo = titulos_comunes[token]
            break
        elif token_base in titulos_comunes:
            tipo_articulo = titulos_comunes[token_base]
            break

    if revista == "rmde":
        from Modules.journals.rmde.html_processor import procesar_html as procesar_rmde
        def procesador_wrapper_rmde(**kwargs):
            if not kwargs.get("tipo_articulo_forzado"):
                kwargs["tipo_articulo_forzado"] = tipo_articulo
            return procesar_rmde(**kwargs)
        return procesador_wrapper_rmde

    elif revista == "cc":
        from Modules.journals.cc.html_processor import procesar_html as procesar_cc
        def procesador_wrapper_cc(**kwargs):
            if not kwargs.get("tipo_articulo_forzado"):
                kwargs["tipo_articulo_forzado"] = tipo_articulo
            return procesar_cc(**kwargs)
        return procesador_wrapper_cc

    else:
        raise ValueError(f"La revista '{revista}' no está soportada en el sistema.")