"""
Módulo central para la gestión y enrutamiento de secciones de revistas.
Identifica el tipo de artículo dinámicamente escaneando la ruta completa del archivo y la carpeta.
"""

import re
import os
from typing import Callable

def obtener_procesador_por_seccion(revista: str, codigo_seccion: str) -> Callable:
    
    # Mapeo universal de abreviaturas (Fronteras de palabra \b para evitar falsos positivos)
    titulos_comunes = {
        r'\bcj\b': "Comentario jurisprudencial",
        r'\bcl\b': "Comentario legislativo",
        r'\brb\b': "Reseña bibliográfica",
        r'\bnm\b': "Nota metodológica",
        r'\bej\b': "Estudio jurisprudencial",
        r'\bar\b': "Análisis regional",
        r'\boe\b': "Observatorio electoral",
        r'\bart\b': "Artículo"
    }

    def detectar_tipo(cadena: str) -> str:
        """Busca patrones de abreviaturas en una cadena normalizada."""
        # Convierte guiones bajos y normales en espacios para aislar la abreviatura
        cadena_limpia = cadena.lower().replace('_', ' ').replace('-', ' ')
        for patron, titulo in titulos_comunes.items():
            if re.search(patron, cadena_limpia):
                return titulo
        return "Artículo" # Valor por defecto seguro

    if revista == "rmde":
        from Modules.journals.rmde.html_processor import procesar_html as procesar_rmde
        def procesador_wrapper_rmde(**kwargs):
            ruta = kwargs.get("html_path", "")
            carpeta = os.path.basename(os.path.dirname(ruta)) if ruta else ""
            archivo = os.path.basename(ruta) if ruta else ""
            # Escanea la carpeta, el archivo y el código enviado por si acaso
            contexto_busqueda = f"{carpeta} {archivo} {codigo_seccion}"
            kwargs["tipo_articulo_forzado"] = detectar_tipo(contexto_busqueda)
            return procesar_rmde(**kwargs)
        return procesador_wrapper_rmde

    elif revista == "cc":
        from Modules.journals.cc.html_processor import procesar_html as procesar_cc
        def procesador_wrapper_cc(**kwargs):
            ruta = kwargs.get("html_path", "")
            carpeta = os.path.basename(os.path.dirname(ruta)) if ruta else ""
            archivo = os.path.basename(ruta) if ruta else ""
            # Escanea la carpeta, el archivo y el código enviado por si acaso
            contexto_busqueda = f"{carpeta} {archivo} {codigo_seccion}"
            kwargs["tipo_articulo_forzado"] = detectar_tipo(contexto_busqueda)
            return procesar_cc(**kwargs)
        return procesador_wrapper_cc

    else:
        raise ValueError(f"La revista '{revista}' no está soportada.")