"""
Módulo para procesar y corregir archivos CSS específicos de Cuestiones Constitucionales (CC).
"""

import os
import re
from typing import List, Dict

_BASE_FONT_PX = 12.0

# Mapeo basado en el CSS generado para CC
_FONT_SIZE_MAP: Dict[str, str] = {
    "7px": "0.6em",
    "9px": "0.8em",
    "10px": "0.9em",
    "11px": "1.0em",
}

_MARGIN_MAP: Dict[str, str] = {
    "0": "0",
    "3px": "0.25em",
    "6px": "0.5em",
    "12px": "1.0em",
    "14px": "1.2em",
    "15px": "1.25em",
    "18px": "1.5em",
    "24px": "2.0em",
    "28px": "2.3em",
    "29px": "2.4em",
    "40px": "3.3em",
    "46px": "3.8em",
}

def _px_a_em(valor_px: str) -> str:
    match = re.match(r"^(-?\d+(?:\.\d+)?)px$", valor_px.strip())
    if not match:
        return valor_px
    px_val = float(match.group(1))
    if px_val == 0:
        return "0"
    em_val = round(px_val / _BASE_FONT_PX, 1)
    return f"{em_val}em"

def corregir_css(contenido_css: str) -> str:
    css = contenido_css
    
    # Correcciones de color transparentes a negros
    css = re.sub(r'color:\s*#0000\b', 'color:#000000', css)
    css = re.sub(r'border-color:\s*#0000\b', 'border-color:#000000', css)
    
    # Reemplazo de tamaños de fuente
    for px_val, em_val in _FONT_SIZE_MAP.items():
        css = re.sub(rf'font-size:\s*{re.escape(px_val)}', f'font-size:{em_val}', css)

    def _reemplazar_margin(match: re.Match) -> str:
        prop = match.group(1)
        valor = match.group(2).strip()
        if valor in _MARGIN_MAP:
            return f'{prop}:{_MARGIN_MAP[valor]}'
        return f'{prop}:{_px_a_em(valor)}'

    # Reemplazo de márgenes e indentaciones
    css = re.sub(
        r'(margin-(?:top|bottom|left|right)|text-indent|padding-(?:top|bottom|left|right)):\s*(-?\d+(?:\.\d+)?px)',
        _reemplazar_margin,
        css,
    )
    return css

def generar_css_referencia() -> str:
    return """/* ============================================
   CSS adicional — Formato de referencia Cuestiones Constitucionales
   ============================================ */

.contenedor {
    position: relative;
    padding: 3em 5% 2em 5%;
    max-width: 100%;
    width: 100%;
    box-sizing: border-box;
    margin: 0 auto;
    font-family: Garamond, 'EB Garamond', 'Times New Roman', serif;
    font-size: 16px;
    line-height: 1.58;
    overflow-wrap: break-word;
    word-wrap: break-word;
}

/* Títulos */
h1.titulo_espanol {
    font-family: Garamond, 'EB Garamond', 'Times New Roman', serif;
    font-size: 2em !important;
    font-weight: bold !important;
    text-align: center !important;
    line-height: 1.22 !important;
    margin: 0.8em 0 0.15em 0;
    text-transform: uppercase;
}

h2.titulo_ingles {
    font-family: Garamond, 'EB Garamond', 'Times New Roman', serif;
    font-size: 1.25em !important;
    font-style: italic;
    font-weight: normal;
    text-align: center !important;
    line-height: 1.2;
    margin: 0 0 1.4em 0;
    text-transform: uppercase;
}

/* Autores */
p.AUT, p.AUT-DOS-NOMBRES {
    text-align: center !important;
    margin-top: 1.2em !important;
    margin-bottom: 0.2em !important;
    font-size: 1.05em !important;
    font-weight: bold;
}

p.ORCID, p.ORCID2 {
    text-align: center !important;
    margin-bottom: 0.2em !important;
    margin-top: 0.2em !important;
}

.ORCID ._idSVGInline, .ORCID2 ._idSVGInline {
    display: inline-block;
    width: 1em;
    height: 1em;
}

.ORCID svg, .ORCID2 svg {
    width: 100%;
    height: 100%;
    display: block;
}

p.nota-de-autor-final {
    text-align: center !important;
    font-size: 0.9em;
    margin-top: 0;
    margin-bottom: 0.2em;
}

/* Fechas y DOI */
p.recepcion, p.aceptacion-publicacion, p.DOI {
    text-align: right !important;
    font-size: 0.85em;
    color: #555;
    margin: 0.2em 0;
}

/* Resumen, Palabras clave, Cuerpo y Referencias */
p.resumen, p.resumen_ingles, p.palabras-clave, p.keywords, 
p.BODY-text, p.PP, p.SUMARIO, p.referencias {
    text-align: justify !important;
    text-align-last: left !important;
    hyphens: auto;
    -webkit-hyphens: auto;
    font-size: 1em;
    line-height: 1.6;
    margin-bottom: 1em;
}

p.SUMARIO {
    margin-left: 2em;
    margin-right: 2em;
    font-size: 0.9em;
}

/* Encabezados internos */
h3.romanos {
    text-align: center !important;
    font-variant: small-caps;
    font-size: 1.15em;
    margin-top: 2em;
    margin-bottom: 1em;
}

h4.arabigos {
    text-align: left !important;
    font-variant: small-caps;
    font-size: 1.05em;
    margin-top: 1.5em;
    margin-bottom: 1em;
}

/* Citas largas */
p.trun {
    margin-left: 2em !important;
    margin-right: 2em !important;
    font-size: 0.9em !important;
    text-align: justify !important;
    line-height: 1.4;
}

/* Cómo Citar */
p.como_citar {
    text-align: center !important;
    font-weight: bold;
    color: #425c8a;
    margin-top: 2.5em;
}

p.iijunam, p.APA {
    font-weight: bold;
    color: #003061;
    margin-top: 1em;
}

/* Imágenes y Tablas */
img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 1.4em auto !important;
}

table {
    width: 100% !important;
    border-collapse: collapse !important;
    margin: 1.4em 0 !important;
}

.table-responsive {
    width: 100%;
    overflow-x: auto;
}

section._idFootnotes {
    margin-top: 2em;
    border-top: 1px solid #ccc;
    padding-top: 1em;
    text-align: justify !important;
    font-size: 0.85em;
}

a {
    color: #275b9b;
    text-decoration: none;
}
a:hover {
    text-decoration: underline;
}

span.Hiperv-nculo {
    color: #275b9b;
    text-decoration: underline;
}

hr.HorizontalRule-1 {
    border: none;
    border-top: 1px solid #999;
    margin: 2em 0 1em 0;
}

.Marco-de-texto-b-sico {
    position: absolute;
    top: 0;
    left: 0;
    z-index: 100;
}
.Marco-de-texto-b-sico p.body_text2 {
    background-color: #386abd;
    color: #ffffff;
    padding: 0.6em 1.2em;
    font-family: Garamond, 'EB Garamond', 'Times New Roman', serif;
    font-size: 1.35em;
    font-weight: bold;
    writing-mode: horizontal-tb;
    border-radius: 0 4px 4px 0;
    margin: 0;
    display: inline-block;
}
"""

def procesar_y_combinar_css(rutas_css_origen: List[str]) -> str:
    css_final = []
    for ruta_css in rutas_css_origen:
        try:
            with open(ruta_css, "r", encoding="utf-8") as f:
                css_final.append(corregir_css(f.read()))
        except (IOError, UnicodeDecodeError):
            continue
    css_final.append(generar_css_referencia())
    return "\n".join(css_final)