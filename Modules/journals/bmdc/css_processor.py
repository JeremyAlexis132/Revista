"""
Módulo para procesar y corregir archivos CSS específicos de BMDC.
Unifica la tipografía a Times New Roman, neutraliza formatos residuales de InDesign 
y protege la estructura de la etiqueta de artículo contra herencias globales.
"""

import os
import re
from typing import List, Dict

_BASE_FONT_PX = 12.0

_FONT_SIZE_MAP: Dict[str, str] = {
    "7px": "0.6em", "9px": "0.8em", "10px": "0.9em", "11px": "1.0em",
}

def corregir_css(contenido_css: str) -> str:
    css = contenido_css
    css = re.sub(r'color:\s*#0000\b', 'color:#000000', css)
    css = re.sub(r'border-color:\s*#0000\b', 'border-color:#000000', css)
    
    for px_val, em_val in _FONT_SIZE_MAP.items():
        css = re.sub(rf'font-size:\s*{re.escape(px_val)}', f'font-size:{em_val}', css)

    # Eliminar sangrías (text-indent) de origen
    css = re.sub(r'text-indent:\s*(-?\d+(?:\.\d+)?px|em)', 'text-indent:0', css)
    return css

def generar_css_referencia() -> str:
    return """/* ============================================
   CSS adicional — Formato visual unificado BMDC
   ============================================ */

.contenedor, div[id^="_idContainer"] {
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
    font-size: 16px; 
    line-height: 1.6;
    word-wrap: break-word;
}

/* UNIFICACIÓN A TIMES NEW ROMAN EN TODO EL TEXTO */
*, p, div, span, h1, h2, h3, h4, h5, h6, li, table, td, th {
    font-family: 'Times New Roman', Times, serif !important;
}

/* ELIMINACIÓN DE SANGRÍAS Y UNIFICACIÓN DE TAMAÑO */
p, p.resumen, p.resumen_ingles, p.palabras-clave, p.keywords, 
p.BODY-text, p.PP, p.body_text, p[class*="PP"], p[class*="BODY"], p[class*="body"],
p.SUMARIO, p.referencias, p[class*="bibliografia"], p.NOTA-AL-PIE, section._idFootnotes p, 
.como_citar_section p, p.iijunam, p.APA, ol._listStyleNone {
    text-align: justify !important;
    text-align-last: left !important;
    font-size: 1.1em !important; 
    line-height: 1.6 !important;
    text-indent: 0 !important; 
    margin-left: 0 !important;   
    margin-right: 0 !important;
    padding-left: 0 !important;
    margin-bottom: 1em !important;
}

/* CITAS TEXTUALES Y TRANSCRIPCIONES */
p.trs, p.trul, p.trun, p.TRP, p[class*="trun"], p[class*="trul"], p[class*="trs"], p[class*="TRP"], p[class*="transcripci"], blockquote {
    font-size: 0.95em !important; 
    margin-left: 2.5em !important; 
    margin-right: 2.5em !important;
    text-align: justify !important;
    line-height: 1.5 !important;
    text-indent: 0 !important;
}

.grises-vv, .bold-grises-redondas, .bold-grises-italicas, .BOLD-ITALIC,
strong.grises-vv, strong.bold-grises-redondas, span.bold-grises-italicas, strong.BOLD-ITALIC,
p.resumen *, p.resumen_ingles *, p.palabras-clave *, p.keywords *, p.SUMARIO * {
    font-weight: normal !important;
    color: #000000 !important;
}

p.notas_iniciales {
    text-align: left !important;
    color: #58595b;
    font-size: 1.1em !important;
    line-height: 1.6;
    margin-top: 0 !important;
    margin-bottom: 2em;
}
p.notas_iniciales a, p.notas_iniciales span.hipervinculo {
    color: #215e9e;
    text-decoration: underline;
}

/* CORRECCIÓN DE TÍTULO Y SUBTÍTULO */
h1.titulo_espanol, h1[class*="titulo"], .titulo {
    text-align: left !important;
    font-size: 2.2em !important;
    font-weight: bold !important;
    line-height: 1.2 !important;
    margin: 1em 0 0.2em 0 !important;
    color: #000000 !important;
    -webkit-hyphens: none !important;
    hyphens: none !important;
}

h2.titulo_ingles, h2[class*="titulo"], .subtitulo, .article-subtitle {
    text-align: left !important;
    font-size: 1.5em !important;
    font-style: italic !important;
    font-weight: normal !important;
    line-height: 1.2 !important;
    margin: 0 0 1.5em 0 !important;
    color: #000000 !important;
}

h1.titulo_espanol strong, h1.titulo_espanol span,
h2.titulo_ingles strong, h2.titulo_ingles span {
    font-size: 1em !important;
    margin: 0 !important;
}

/* TÍTULOS DE SECCIONES AUMENTADOS */
h3.romanos, h3.VV, h3[class*="VV"], h3[class*="romano"] {
    text-align: left !important;
    font-size: 1.5em !important;
    font-weight: bold !important;
    margin-top: 1.6em !important;
    margin-bottom: 0.8em !important;
    color: #000000 !important;
}

h4.arabigos, h4.IA, h4[class*="IA"], h4[class*="arabigo"] {
    text-align: left !important;
    font-size: 1.3em !important;
    font-weight: bold !important;
    margin-top: 1.4em !important;
    margin-bottom: 0.8em !important;
    color: #000000 !important;
}

/* =====================================================================
   BLOQUE DE AUTOR: RESTRICCIÓN DE NEGRITAS Y ESPACIADOS
   ===================================================================== */
p.AUT-DOS-NOMBRES, .AUT-DOS-NOMBRES, p.AUT, .AUT, p[class*="aut-dos-nombres"] {
    text-align: left !important;
    font-size: 1.2em !important;
    font-variant: small-caps !important;
    font-weight: normal !important;
    color: #000000 !important;
    margin-top: 1em !important;
    margin-bottom: 0 !important;
    text-indent: 0 !important;
}

.AUT-DOS-NOMBRES strong, .AUT-DOS-NOMBRES b,
.AUT strong, .AUT b,
p[class*="aut-dos-nombres"] strong, p[class*="aut-dos-nombres"] b {
    font-family: inherit !important;
    font-size: 1em !important;
    font-variant: small-caps !important;
    font-weight: bold !important; 
    font-style: normal !important;
    color: #000000 !important;
    letter-spacing: normal !important;
    margin: 0 !important;
}

.AUT-DOS-NOMBRES span:not(._idSVGInline), 
.AUT span:not(._idSVGInline),
p[class*="aut-dos-nombres"] span:not(._idSVGInline) {
    font-family: inherit !important;
    font-size: 1em !important;
    font-variant: small-caps !important;
    font-weight: normal !important;
    font-style: normal !important;
    color: #000000 !important;
    letter-spacing: normal !important;
    margin: 0 !important;
}

.ORCID svg, ._idSVGInline svg {
    width: 16px !important;
    height: 16px !important;
    display: inline-block !important;
}

p.nota-de-autor-final, p.correo, p.adscripcion, p[class*="nota-de-autor"] {
    text-align: left !important;
    margin-top: 0.1em !important;
    margin-bottom: 0.2em !important;
    font-size: 1.1em !important;
    line-height: 1.35 !important;
}

/* FECHAS REUBICADAS (SECCIÓN INFERIOR) */
p.recepcion, p.aceptacion-publicacion, p[class*="recepcion"], .bloque-fechas-inferior p {
    text-align: left !important;
    font-size: 1.1em !important;
    line-height: 1.6 !important;
    color: #000;
    margin-left: 0 !important;
    text-indent: 0 !important;
    margin-bottom: 0.2em !important;
}

.como_citar_section {
    margin-top: 1em;
    margin-bottom: 0.5em;
}
p.como_citar, h3[class*="como_citar"] {
    margin-top: 1.6em !important;
    margin-bottom: 0.4em !important;
    font-variant: small-caps !important;
    text-align: left !important;
    font-size: 1.1em !important;
}

a, span.Hiperv-nculo, span.hipervinculo {
    color: #215e9e !important;
    text-decoration: underline !important;
}

p.SUMARIO a, p.SUMARIO span.Hiperv-nculo, p.SUMARIO span.hipervinculo,
.sumario a, .sumario span.Hiperv-nculo, .sumario span.hipervinculo {
    color: #000000 !important;
    text-decoration: none !important;
    pointer-events: none; 
}

sup, sub, sup.NOTA, span.NUMERO-NOTA, span._idGenCharOverride-1, sup._idGenCharOverride-1, span._idGenCharOverride-2 {
    font-size: 1.05em !important; 
    vertical-align: super !important;
    line-height: 0;
}

hr.HorizontalRule-1 {
    border: none;
    border-top: 1px solid #999;
    margin: 2em 0 1em 0;
}

/* ==========================================================
   ETIQUETA DE TIPO DE ARTÍCULO SUPERIOR (Protección estricta)
   ========================================================== */
.Marco-de-texto-b-sico {
    position: absolute !important; 
    top: 0 !important; 
    left: 0 !important; 
    z-index: 100 !important;
    margin: 0 !important;
    padding: 0 !important;
}
.Marco-de-texto-b-sico p.body_text2, 
.Marco-de-texto-b-sico p[class*="body"] {
    background-color: #386abd !important; 
    color: #ffffff !important;
    padding: 0.6em 1.2em !important; 
    font-size: 1.35em !important; 
    font-weight: bold !important;
    border-radius: 0 4px 4px 0 !important; 
    margin: 0 !important; 
    display: inline-block !important;
    text-align: left !important;
    text-indent: 0 !important;
    line-height: normal !important;
}
.Marco-de-texto-b-sico p.body_text2 span, 
.Marco-de-texto-b-sico p[class*="body"] span {
    font-size: 1em !important;
    font-family: inherit !important;
    font-variant: normal !important;
    letter-spacing: normal !important;
    color: #ffffff !important;
}

/* =========================================================================
   TABLAS RESPONSIVE Y MULTIMEDIA
   ========================================================================= */
img {
    max-width: 100%; height: auto;
    margin: 1.4em auto !important; display: block;
}

.table-responsive {
    width: 100%;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    display: block;
    margin: 1.4em 0;
}

table {
    width: 100% !important;
    border-collapse: collapse !important;
    margin: 0 !important;
}

table td, table th {
    font-size: 1.1em !important;
    text-align: justify !important;
    padding: 0.6em !important;
}

@media (max-width: 768px) {
    table {
        min-width: 600px !important;
    }
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