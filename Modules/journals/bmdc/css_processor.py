"""
Módulo para procesar y corregir archivos CSS específicos de BMDC.
Unifica la tipografía a Times New Roman, neutraliza herencias de InDesign
y corrige el espaciado de autores, resúmenes, referencias y notas al pie.
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

/* Forzar Times New Roman en TODO el documento, anulando herencias de InDesign */
*, *::before, *::after {
    font-family: 'Times New Roman', Times, serif !important;
    box-sizing: border-box;
}

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

/* DESTRUCCIÓN GLOBAL DE SANGRÍAS */
p {
    text-indent: 0 !important;
}

/* =========================================================================
   TÍTULOS (Neutralización de centrado, sangrías y tamaños anómalos)
   ========================================================================= */
h1.titulo_espanol {
    font-family: 'Times New Roman', Times, serif !important;
    font-size: 1.7em !important;
    font-weight: bold !important;
    text-align: left !important;
    text-indent: 0 !important;
    margin-left: 0 !important;
    padding-left: 0 !important;
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
    text-indent: 0 !important;
    margin-left: 0 !important;
    padding-left: 0 !important;
    line-height: 1.2 !important;
    margin: 0 0 1.4em 0 !important;
    color: #000000 !important;
}

h1.titulo_espanol * { font-size: 1em !important; text-align: left !important; font-weight: bold !important; text-indent: 0 !important; margin-left: 0 !important; padding-left: 0 !important; }
h2.titulo_ingles * { font-size: 1em !important; text-align: left !important; font-style: italic !important; font-weight: normal !important; text-indent: 0 !important; margin-left: 0 !important; padding-left: 0 !important; }

/* =========================================================================
   AUTORES
   ========================================================================= */
p.AUT-DOS-NOMBRES, p.AUT, p.autor_item {
    font-family: 'Times New Roman', Times, serif !important;
    font-size: 1.2em !important;
    font-variant: small-caps !important;
    font-weight: bold !important;
    font-style: normal !important;
    text-align: left !important;
    color: #000000 !important;
    margin-top: 1.5em !important;
    margin-bottom: 0 !important;
    padding: 0 !important;
    line-height: 1.4 !important;
    text-indent: 0 !important;
}

p.AUT-DOS-NOMBRES *, p.AUT *, p.autor_item * {
    font-size: 1em !important;
    font-variant: inherit !important;
    font-weight: inherit !important;
    font-style: normal !important;
}

p.nota-de-autor-final {
    font-family: 'Times New Roman', Times, serif !important;
    font-size: 1em !important;
    font-weight: normal !important;
    text-align: left !important;
    color: #000000 !important;
    margin-top: 0 !important;
    margin-bottom: 0 !important;
    padding: 0 !important;
    line-height: 1.35 !important;
    text-indent: 0 !important;
}

p.AUT-DOS-NOMBRES *, p.nota-de-autor-final * {
    font-size: 1em !important; text-align: left !important; font-family: inherit !important;
}

/* =========================================================================
   TEXTO GENERAL Y RESÚMENES
   ========================================================================= */
p.resumen, p.resumen_ingles, p.palabras-clave, p.keywords, p.abstract,
p.BODY-text, p.PP, p.body_text, p.ESTILOS-FINALES_BODY-text,
p.SUMARIO, p.referencias, 
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

/* SEPARACIÓN EXACTA DE 1 ENTER ENTRE AUTORES Y RESUMEN */
p.resumen, p.abstract {
    margin-top: 1.6em !important;
    margin-bottom: 0.8em !important;
}

p.palabras-clave, p.resumen_ingles, p.keywords {
    margin-top: 0.8em !important; 
    margin-bottom: 0.8em !important;
}

/* Anular el efecto miniatura de los spans de InDesign */
p.resumen *, p.resumen_ingles *, p.palabras-clave *, p.keywords *, p.abstract *,
p.BODY-text *, p.PP *, p.body_text *, p.ESTILOS-FINALES_BODY-text *, p.SUMARIO * {
    font-size: 1em !important;
    font-family: 'Times New Roman', Times, serif !important;
    text-indent: 0 !important;
    margin-left: 0 !important;
}

/* =========================================================================
   REFERENCIAS: TEXTO PLANO Y LIGAS ÚNICAMENTE
   ========================================================================= */
p.referencias {
    font-size: 1.1em !important; /* Mismo tamaño normal del cuerpo de texto */
    font-weight: normal !important;
    font-style: normal !important;
    margin-bottom: 0.8em !important;
    text-indent: 0 !important;
    text-align: justify !important;
}

p.referencias * {
    font-size: 1em !important; /* Neutraliza spans gigantes o pequeños */
    font-weight: normal !important; 
    font-style: normal !important;
    text-decoration: none !important;
}

p.referencias a, p.referencias a *, p.referencias span.hipervinculo {
    color: #215e9e !important;
    text-decoration: underline !important;
}

/* =========================================================================
   NOTAS AL PIE
   ========================================================================= */
p.NOTA-AL-PIE, p.ESTILOS-FINALES_NOTA-AL-PIE, section._idFootnotes p, section._idFootnotes div {
    font-family: 'Times New Roman', Times, serif !important;
    font-size: 0.95em !important; /* Ligeramente más pequeñas que el texto plano (1.1em) */
    line-height: 1.4 !important;
    text-align: justify !important;
    text-align-last: left !important;
    text-indent: 0 !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
    padding-left: 0 !important;
    margin-top: 0.3em !important;
    margin-bottom: 0.6em !important;
    color: #000000 !important;
}

p.NOTA-AL-PIE *, p.ESTILOS-FINALES_NOTA-AL-PIE *, section._idFootnotes p * {
    font-size: 1em !important; /* Congela el tamaño para que herede el 0.95em */
    font-family: 'Times New Roman', Times, serif !important;
}

/* Superíndices (Números de nota) en todo el documento y dentro de notas al pie */
sup, sub, sup.NOTA, span.NUMERO-NOTA, span._idGenCharOverride-1, sup._idGenCharOverride-1, span._idGenCharOverride-2 {
    font-size: 0.75em !important; /* Números reducidos para no interrumpir el interlineado */
    vertical-align: super !important;
    line-height: 0;
}

/* =========================================================================
   CITAS, SECCIONES Y MULTIMEDIA
   ========================================================================= */
p.ESTILOS-FINALES_TRP, p.ESTILOS-FINALES_trs, p.ESTILOS-FINALES_trul, p.ESTILOS-FINALES_trun,
[class*="TRP"], [class*="_trs"], [class*="_trul"], [class*="_trun"] {
    font-family: 'Times New Roman', Times, serif !important;
    font-size: 0.95em !important;
    line-height: 1.5 !important;
    text-align: justify !important;
    margin-left: 2em !important;
    margin-right: 1em !important;
    padding-left: 0 !important;
    color: #000000 !important;
    text-indent: 0 !important;
}

.grises-vv, .bold-grises-redondas, .bold-grises-italicas, .BOLD-ITALIC {
    font-weight: normal !important; color: #000000 !important; font-family: 'Times New Roman', Times, serif !important;
}

h3.romanos, h4.arabigos { 
    text-align: left !important; 
    text-indent: 0 !important; 
    margin-left: 0 !important; 
    padding-left: 0 !important; 
    color: #000000 !important;
}
h3.romanos *, h4.arabigos * {
    text-align: left !important;
    text-indent: 0 !important;
    font-size: 1em !important;
    color: #000000 !important;
}
h3.romanos { font-size: 1.35em !important; margin-top: 1.6em !important; margin-bottom: 0.8em !important; font-weight: bold !important;}
h4.arabigos { font-size: 1.25em !important; margin-top: 1.2em !important; margin-bottom: 0.8em !important; font-weight: bold !important;}


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

p.SUMARIO a, p.SUMARIO span.Hiperv-nculo, p.SUMARIO span.hipervinculo, .sumario a {
    color: #000000 !important; text-decoration: none !important; pointer-events: none;
}

hr.HorizontalRule-1 { border: none; border-top: 1px solid #999; margin: 2em 0 1em 0; }
.Marco-de-texto-b-sico { position: absolute; top: 0; left: 0; z-index: 100; }
.Marco-de-texto-b-sico p.body_text2 {
    background-color: #386abd; color: #ffffff; padding: 0.6em 1.2em; font-family: 'Times New Roman', Times, serif !important;
    font-size: 1.35em; font-weight: bold; border-radius: 0 4px 4px 0; margin: 0; display: inline-block;
}

img { max-width: 100%; height: auto; margin: 1.4em 0 !important; display: block; }
/* Párrafos contenedores de imagen real del artículo */
p.imagen-articulo {
    margin: 1.4em 0 0.3em 0 !important;
    padding: 0 !important;
    text-indent: 0 !important;
    text-align: left !important;
}
p.imagen-articulo img {
    margin: 0 !important;
    display: block;
    max-width: 100%;
    height: auto;
}
/* Pies de figura / fuentes */
p.pie-figura {
    font-family: 'Times New Roman', Times, serif !important;
    font-size: 0.95em !important;
    line-height: 1.4 !important;
    text-align: left !important;
    text-indent: 0 !important;
    margin: 0 0 1.2em 0 !important;
    color: #000000 !important;
}
p.pie-figura * { font-size: 1em !important; font-family: inherit !important; }
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