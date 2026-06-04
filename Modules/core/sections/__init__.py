"""
Módulo central para la gestión y enrutamiento de secciones de revistas.
"""

from typing import Callable

def obtener_procesador_por_seccion(revista: str, codigo_seccion: str) -> Callable:
    """
    Fábrica que devuelve la función procesadora adecuada según la revista y el código de sección.
    """
    if revista == "rmde":
        from Modules.journals.rmde.html_processor import procesar_html as procesar_rmde
        
        # Mapeo de códigos de carpeta a títulos formales para RMDE
        titulos_rmde = {
            "art": "Artículo",
            "nm": "Nota metodológica",
            "ej": "Estudio jurisprudencial",
            "ar": "Análisis regional",
            "oe": "Observatorio electoral"
        }
        
        def procesador_wrapper_rmde(**kwargs):
            if "tipo_articulo_forzado" not in kwargs:
                kwargs["tipo_articulo_forzado"] = titulos_rmde.get(codigo_seccion, "Artículo")
            return procesar_rmde(**kwargs)
            
        return procesador_wrapper_rmde

    elif revista == "cc":
        from Modules.journals.cc.html_processor import procesar_html as procesar_cc
        
        def procesador_wrapper_cc(**kwargs):
            # Cuestiones Constitucionales infiere el tipo de artículo internamente 
            # desde su propio html_processor, por lo que no forzamos la etiqueta aquí.
            return procesar_cc(**kwargs)
            
        return procesador_wrapper_cc

    else:
        raise ValueError(f"La revista '{revista}' no está soportada en el sistema.")