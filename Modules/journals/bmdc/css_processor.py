"""
Módulo para procesar y corregir archivos CSS específicos de BMDC.
Unifica la tipografía a Times New Roman, neutraliza herencias de InDesign
y corrige el espaciado de autores.
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
   CSS adicional — Formato visual unificado BMDC
   ============================================ */

.contenedor, div[id^="_idContainer"], div[class^="_idGenObjectStyleOverride"] {
    width: 100% !important;
    max-width: 100% !important;
    display: block !important;
    position: relative;
}

.contenedor {
    padding: 3em 5% 2em 5%;
    box-sizing: border-box;
    margin: 0 auto;
    font-family: 'Times New Roman', Times, serif !important;
    font-size: 18px;
    line-height: 1.6;
    word-wrap: break-word;
}

/* =========================================================================
   TÍTULOS (Neutralización de centrado y tamaños anómalos)
   ========================================================================= */
h1.titulo_espanol {
    font-family: 'Times New Roman', Times, serif !important;
    font-size: 1.7em !important;
    font-weight: bold !important;
    text-align: left !important;
    line-height: 1.22 !important;
    margin: 0.8em 0 0.15em 0 !important;
    color: #000000 !important;
    -webkit-hyphens: none !important;
    hyphens: none !important;
}

h2.titulo_ingles {
    font-family: 'Times New Roman', Times, serif !important;
    font-size: 1.25em !important;
    font-style: italic !important;
    font-weight: normal !important;
    text-align: left !important;
    line-height: 1.2 !important;
    margin: 0 0 1.4em 0 !important;
    color: #000000 !important;
}

/* Forzar todo lo que está dentro del título a respetar la jerarquía (ignorar spans internos) */
h1.titulo_espanol * { font-size: 1em !important; text-align: left !important; font-weight: bold !important; }
h2.titulo_ingles * { font-size: 1em !important; text-align: left !important; font-style: italic !important; font-weight: normal !important; }

/* =========================================================================
   AUTORES (Sin espacio entre sus datos, margen solo por arriba)
   ========================================================================= */
p.AUT-DOS-NOMBRES, p.AUT {
    font-family: 'Times New Roman', Times, serif !important;
    font-size: 1.2em !important;
    font-variant: small-caps !important;
    font-weight: bold !important;
    text-align: left !important;
    color: #000000 !important;
    margin-top: 1.5em !important; /* Espacio para separar de otros autores o el título */
    margin-bottom: 0 !important;  /* PEGADO a su afiliación */
    padding: 0 !important;
}

p.nota-de-autor-final {
    font-family: 'Times New Roman', Times, serif !important;
    font-size: 1em !important;
    font-weight: normal !important;
    text-align: left !important;
    color: #000000 !important;
    margin-top: 0 !important; /* PEGADO a la línea de arriba */
    margin-bottom: 0 !important; /* PEGADO al correo */
    padding: 0 !important;
    line-height: 1.35 !important;
}

p.AUT-DOS-NOMBRES *, p.nota-de-autor-final * {
    font-size: 1em !important; text-align: left !important; font-family: inherit !important;
}

/* =========================================================================
   TEXTO GENERAL Y REFERENCIAS
   ========================================================================= */
p.resumen, p.resumen_ingles, p.palabras-clave, p.keywords, 
p.BODY-text, p.PP, p.body_text,
p.SUMARIO, p.referencias, p.NOTA-AL-PIE, section._idFootnotes p, 
.como_citar_section p, p.iijunam, p.APA, ol._listStyleNone {
    font-family: 'Times New Roman', Times, serif !important;
    text-align: justify !important;
    text-align-last: left !important;
    hyphens: auto;
    font-size: 1.1em !important;
    line-height: 1.6 !important;
    text-indent: 0 !important;   
    margin-left: 0 !important;   
    margin-right: 0 !important;
    padding-left: 0 !important;
}

.grises-vv, .bold-grises-redondas, .bold-grises-italicas, .BOLD-ITALIC,
h3.romanos, h3.romanos *, h4.arabigos, h4.arabigos *, p.resumen *, p.SUMARIO * {
    font-weight: normal !important; color: #000000 !important; font-family: 'Times New Roman', Times, serif !important;
}

h3.romanos { font-size: 1.35em !important; margin-top: 1.6em !important; margin-bottom: 0.8em !important; text-align: left !important; }
h4.arabigos { font-size: 1.25em !important; margin-top: 1.2em !important; margin-bottom: 0.8em !important; text-align: left !important; }

p.notas_iniciales { color: #58595b; font-size: 1.1em !important; line-height: 1.6; margin-top: 0 !important; margin-bottom: 2em; text-align: left !important;}
p.notas_iniciales a, p.notas_iniciales span.hipervinculo { color: #215e9e; text-decoration: underline; }

p.recepcion, p.aceptacion-publicacion {
    font-family: 'Times New Roman', Times, serif !important; text-align: left !important;
    font-size: 1.1em !important; line-height: 1.6 !important; color: #000; margin-left: 0 !important; text-indent: 0 !important;
}

.como_citar_section { margin-top: 1em; margin-bottom: 0.5em; }
p.como_citar {
    font-family: 'Times New Roman', Times, serif !important; margin-top: 1.6em !important; margin-bottom: 0.4em !important;
    font-size: 1.1em !important; font-variant: small-caps !important; text-align: left !important; text-indent: 0 !important;
}

.ORCID ._idSVGInline, ._idSVGInline { display: inline-block; width: 1em; height: 1em; }
.ORCID svg, ._idSVGInline svg { width: 100%; height: 100%; display: block; }
a, span.Hiperv-nculo, span.hipervinculo { color: #215e9e !important; text-decoration: underline !important; }

/* Neutralización sumario */
p.SUMARIO a, p.SUMARIO span.Hiperv-nculo, p.SUMARIO span.hipervinculo, .sumario a {
    color: #000000 !important; text-decoration: none !important; pointer-events: none;
}

sup, sub, sup.NOTA, span.NUMERO-NOTA, span._idGenCharOverride-1, sup._idGenCharOverride-1, span._idGenCharOverride-2 {
    font-size: 1.05em !important; vertical-align: super !important; line-height: 0;
}

hr.HorizontalRule-1 { border: none; border-top: 1px solid #999; margin: 2em 0 1em 0; }
.Marco-de-texto-b-sico { position: absolute; top: 0; left: 0; z-index: 100; }
.Marco-de-texto-b-sico p.body_text2 {
    background-color: #386abd; color: #ffffff; padding: 0.6em 1.2em; font-family: 'Times New Roman', Times, serif !important;
    font-size: 1.35em; font-weight: bold; border-radius: 0 4px 4px 0; margin: 0; display: inline-block;
}

img { max-width: 100%; height: auto; margin: 1.4em auto !important; display: block; }
.table-responsive { width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch; display: block; margin: 1.4em 0; }
table { width: 100% !important; border-collapse: collapse !important; margin: 0 !important; }
table td, table th { font-family: 'Times New Roman', Times, serif !important; font-size: 1em !important; text-align: justify !important; padding: 0.6em !important; }
@media (max-width: 768px) { table { min-width: 600px !important; } }
section._idFootnotes { margin-top: 2em; border-top: 1px solid #ccc; padding-top: 1em; text-align: justify !important; margin-left: 0 !important; padding-left: 0 !important; }
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