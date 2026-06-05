"""
Módulo para procesar y corregir archivos CSS específicos de CC.
Aplica estrictamente la estética, tipografía y alineación visual de RMDE,
eliminando sangrías indeseadas, unificando el estilo de los autores,
ajustando márgenes superiores y deshabilitando negritas en subtítulos.
"""

import os
import re
from typing import List, Dict

_BASE_FONT_PX = 12.0

_FONT_SIZE_MAP: Dict[str, str] = {
    "7px": "0.6em", "9px": "0.8em", "10px": "0.9em", "11px": "1.0em",
}

_MARGIN_MAP: Dict[str, str] = {
    "0": "0", "3px": "0.25em", "6px": "0.5em", "12px": "1.0em",
    "14px": "1.2em", "15px": "1.25em", "18px": "1.5em", "24px": "2.0em",
}

def _px_a_em(valor_px: str) -> str:
    match = re.match(r"^(-?\d+(?:\.\d+)?)px$", valor_px.strip())
    if not match: return valor_px
    px_val = float(match.group(1))
    return "0" if px_val == 0 else f"{round(px_val / _BASE_FONT_PX, 1)}em"

def corregir_css(contenido_css: str) -> str:
    css = contenido_css
    css = re.sub(r'color:\s*#0000\b', 'color:#000000', css)
    css = re.sub(r'border-color:\s*#0000\b', 'border-color:#000000', css)
    
    for px_val, em_val in _FONT_SIZE_MAP.items():
        css = re.sub(rf'font-size:\s*{re.escape(px_val)}', f'font-size:{em_val}', css)

    def _reemplazar_margin(match: re.Match) -> str:
        prop, valor = match.group(1), match.group(2).strip()
        return f'{prop}:{_MARGIN_MAP.get(valor, _px_a_em(valor))}'

    css = re.sub(
        r'(margin-(?:top|bottom|left|right)|text-indent|padding-(?:top|bottom|left|right)):\s*(-?\d+(?:\.\d+)?px)',
        _reemplazar_margin, css
    )
    return css

def generar_css_referencia() -> str:
    return """/* ============================================
   CSS adicional — Formato visual RMDE aplicado a CC (Ajustes Finales)
   ============================================ */

/* Asegurar anchos al 100% para evitar colapsos verticales */
.contenedor, div[id^="_idContainer"], div[class^="_idGenObjectStyleOverride"] {
    width: 100% !important;
    max-width: 100% !important;
    display: block !important;
    position: relative;
}

/* Tamaño de texto general aumentado */
.contenedor {
    padding: 3em 5% 2em 5%;
    box-sizing: border-box;
    margin: 0 auto;
    font-family: Garamond, 'EB Garamond', 'Times New Roman', serif;
    font-size: 17px; 
    line-height: 1.6;
    word-wrap: break-word;
}

/* ==========================================================
   QUITA NEGRITAS: Obliga a texto normal en TODO (subtítulos, introducciones) 
   ========================================================== */
.grises-vv, .bold-grises-redondas, .bold-grises-italicas, .BOLD-ITALIC,
strong.grises-vv, strong.bold-grises-redondas, span.bold-grises-italicas, strong.BOLD-ITALIC,
h2.titulo_ingles, h2.titulo_ingles *,
h3.romanos, h3.romanos *,
h4.arabigos, h4.arabigos *,
p.resumen *, p.resumen_ingles *, p.palabras-clave *, p.keywords *, p.SUMARIO * {
    font-weight: normal !important;
    color: #000000 !important;
}

/* Alineación general a la izquierda (Estilo RMDE) */
h1.titulo_espanol, h2.titulo_ingles, h3.romanos, h4.arabigos,
p.AUT, p.AUT-DOS-NOMBRES, p.ORCID, p.nota-de-autor-final, p.correo, p.adscripcion,
p.recepcion, p.aceptacion-publicacion, p.DOI, p.como_citar, p.iijunam, p.APA, p.notas_iniciales {
    text-align: left !important;
    text-indent: 0 !important;
}

/* Identificadores (Leyenda superior ajustada al margen exacto tras quitar los <br>) */
p.notas_iniciales {
    color: #58595b;
    font-family: Garamond, serif;
    font-size: 1em;
    line-height: 1.6;
    margin-top: 0 !important; /* Ajuste perfecto a la etiqueta superior */
    margin-bottom: 2em;
}
p.notas_iniciales a, p.notas_iniciales span.hipervinculo {
    color: #215e9e;
    text-decoration: underline;
}

/* ==========================================================
   EXCEPCIÓN DE NEGRITAS 1: Título Principal SÍ va en negritas y tamaño ajustado
   ========================================================== */
h1.titulo_espanol {
    font-family: Garamond, 'EB Garamond', 'Times New Roman', serif !important;
    font-size: 1.7em !important;
    font-weight: bold !important;
    line-height: 1.22 !important;
    margin: 0.8em 0 0.15em 0 !important;
    -webkit-hyphens: none !important;
    hyphens: none !important;
}

/* Protege el contenido interno del título para que no herede márgenes extraños */
h1.titulo_espanol strong, h1.titulo_espanol span {
    font-family: inherit !important;
    font-size: 1em !important;
    font-weight: bold !important;
    margin: 0 !important;
}

/* Título en inglés sin negritas */
h2.titulo_ingles {
    font-family: Garamond, 'EB Garamond', 'Times New Roman', serif !important;
    font-size: 1.25em !important;
    font-style: italic !important;
    font-weight: normal !important;
    line-height: 1.2 !important;
    margin: 0 0 1.4em 0 !important;
}

h2.titulo_ingles strong, h2.titulo_ingles span {
    font-family: inherit !important;
    font-size: 1em !important;
    font-style: italic !important;
    font-weight: normal !important;
    margin: 0 !important;
}

/* Subtítulos más grandes pero en texto normal */
h3.romanos {
    font-size: 1.35em !important; 
    margin-top: 1.6em !important;
    margin-bottom: 0.8em !important;
}

h4.arabigos {
    font-size: 1.25em !important;
    margin-top: 1.2em !important;
    margin-bottom: 0.8em !important;
}

/* ==========================================================
   EXCEPCIÓN DE NEGRITAS 2: Uniformidad Total en Autores y arreglo de ORCID
   ========================================================== */
p.AUT, p.AUT-DOS-NOMBRES {
    font-family: Garamond, 'EB Garamond', 'Times New Roman', serif !important;
    font-size: 1.15em !important;
    font-variant: small-caps !important;
    font-weight: bold !important;
    color: #000000 !important;
    margin-top: 1.2em !important;
    margin-bottom: 0.2em !important;
}

p.AUT strong, p.AUT span:not(._idSVGInline), p.AUT-DOS-NOMBRES strong, p.AUT-DOS-NOMBRES span:not(._idSVGInline) {
    font-family: inherit !important;
    font-size: 1em !important;
    font-variant: small-caps !important;
    font-weight: bold !important;
    font-style: normal !important;
    color: #000000 !important;
    letter-spacing: normal !important;
    margin: 0 !important; 
}

/* Blindaje para alinear a la izquierda cualquier variante de información de contacto/adscripción */
p.nota-de-autor-final, p.correo, p.adscripcion {
    margin-top: 0 !important;
    margin-bottom: 0.35em !important;
    font-size: 0.95em !important;
    line-height: 1.35 !important;
    text-align: left !important;
}

/* Cuerpo y Resumen Justificados (Tamaño aumentado) */
p.resumen, p.resumen_ingles, p.palabras-clave, p.keywords, 
p.BODY-text, p.PP {
    font-family: Garamond, 'EB Garamond', 'Times New Roman', serif !important;
    text-align: justify !important;
    text-align-last: left !important;
    hyphens: auto;
    font-size: 1.05em !important; 
    line-height: 1.6 !important;
}

/* Eliminación total de sangrías indeseadas */
p.SUMARIO, p.referencias, p.NOTA-AL-PIE, section._idFootnotes p, 
.como_citar_section p, p.como_citar, p.iijunam, p.APA, ol._listStyleNone {
    margin-left: 0 !important;
    margin-right: 0 !important;
    text-indent: 0 !important;
    padding-left: 0 !important;
    text-align: justify !important;
    text-align-last: left !important;
    font-size: 1em !important;
}

/* Fechas trasladadas al fondo sin sangrías */
p.recepcion, p.aceptacion-publicacion {
    font-family: Garamond, 'EB Garamond', 'Times New Roman', serif !important;
    text-align: left !important;
    font-size: 1em !important;
    line-height: 1.6 !important;
    color: #000;
    margin-left: 0 !important;
    text-indent: 0 !important;
}

/* Transcripciones */
p.trun {
    margin-left: 2.5em !important;
    margin-right: 2.5em !important;
    font-size: 1.05em !important;
    text-align: justify !important;
    line-height: 1.5 !important;
    margin-top: 1.2em !important;
    margin-bottom: 1.2em !important;
    text-indent: 0 !important; 
}

/* Cómo Citar */
.como_citar_section {
    margin-top: 1em;
    margin-bottom: 0.5em;
}
p.como_citar {
    margin-top: 1.6em !important;
    margin-bottom: 0.4em !important;
    font-size: 1.05em !important;
    font-variant: small-caps !important;
}

/* SVG y Enlaces */
.ORCID ._idSVGInline, ._idSVGInline {
    display: inline-block; width: 1em; height: 1em;
}
.ORCID svg, ._idSVGInline svg {
    width: 100%; height: 100%; display: block;
}
a, span.Hiperv-nculo, span.hipervinculo {
    color: #215e9e !important;
    text-decoration: underline !important;
}

/* Superíndices de Notas al pie */
sup, sub, sup.NOTA, span.NUMERO-NOTA, span._idGenCharOverride-1, sup._idGenCharOverride-1, span._idGenCharOverride-2 {
    font-size: 1.05em !important; 
    vertical-align: super !important;
    line-height: 0;
}

/* Misceláneos */
hr.HorizontalRule-1 {
    border: none;
    border-top: 1px solid #999;
    margin: 2em 0 1em 0;
}
.Marco-de-texto-b-sico {
    position: absolute; top: 0; left: 0; z-index: 100;
}
.Marco-de-texto-b-sico p.body_text2 {
    background-color: #386abd; color: #ffffff;
    padding: 0.6em 1.2em; font-family: Garamond, serif;
    font-size: 1.35em; font-weight: bold;
    border-radius: 0 4px 4px 0; margin: 0; display: inline-block;
}
img {
    max-width: 100%; height: auto;
    margin: 1.4em auto !important; display: block;
}
table {
    width: 100% !important;
    max-width: 100%;
    margin: 1.4em 0 !important;
    border-collapse: collapse !important;
}
table td, table th {
    font-family: Garamond, 'EB Garamond', 'Times New Roman', serif !important;
    font-size: 1em !important;
    text-align: justify !important;
    padding: 0.6em !important;
}
section._idFootnotes {
    margin-top: 2em;
    border-top: 1px solid #ccc;
    padding-top: 1em;
    text-align: justify !important;
    margin-left: 0 !important;
    padding-left: 0 !important;
}
"""

def procesar_y_combinar_css(rutas_css_origen: List[str]) -> str:
    css_final = []
    for ruta_css in rutas_css_origen:
        try:
            with open(ruta_css, "r", encoding="utf-8") as f:
                css_final.append(corregir_css(f.read()))
        except (IOError, UnicodeDecodeError): continue
    css_final.append(generar_css_referencia())
    return "\n".join(css_final)