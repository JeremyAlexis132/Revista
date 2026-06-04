"""
Módulo para procesar y corregir archivos CSS específicos de Cuestiones Constitucionales (CC).
"""

import os
import re
from typing import List, Dict

_BASE_FONT_PX = 12.0

_FONT_SIZE_MAP: Dict[str, str] = {
    "5px": "0.55em",
    "7px": "0.6em",
    "9px": "0.9em",
    "10px": "1.1em",
    "11px": "1.2em",
    "12px": "1.3em",
}

_MARGIN_MAP: Dict[str, str] = {
    "0": "0",
    "2px": "0.2em",
    "3px": "0.25em",
    "4px": "0.4em",
    "5px": "0.6em",
    "6px": "0.5em",
    "7px": "0.8em",
    "12px": "1.3em",
    "14px": "1.6em",
    "15px": "1.65em",
    "18px": "2.0em",
    "24px": "2.7em",
    "28px": "3.1em",
    "29px": "3.2em",
    "36px": "4.0em",
    "40px": "4.4em",
    "46px": "5.1em",
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
    css = re.sub(r'color:\s*#0000\b', 'color:#000000', css)
    css = re.sub(r'border-color:\s*#0000\b', 'border-color:#000000', css)
    css = re.sub(
        r'border-(left|right|top|bottom)-color:\s*#0000\b',
        r'border-\1-color:#000000',
        css,
    )

    for px_val, em_val in _FONT_SIZE_MAP.items():
        css = re.sub(
            rf'font-size:\s*{re.escape(px_val)}',
            f'font-size:{em_val}',
            css,
        )

    def _reemplazar_margin(match: re.Match) -> str:
        prop = match.group(1)
        valor = match.group(2).strip()
        if valor in _MARGIN_MAP:
            return f'{prop}:{_MARGIN_MAP[valor]}'
        return f'{prop}:{_px_a_em(valor)}'

    css = re.sub(
        r'(margin-(?:top|bottom|left|right)|text-indent|padding-(?:top|bottom|left|right)):\s*(-?\d+(?:\.\d+)?px)',
        _reemplazar_margin,
        css,
    )

    css = re.sub(
        r'(p\.identificador\s*\{[^}]*?)color:\s*#58595b',
        r'\1color:#58595b',
        css,
    )

    return css

def generar_css_referencia() -> str:
    return """/* ============================================
   CSS adicional — Formato de referencia Homologado CC/RMDE
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

h1, h2, h3, h4, h5, h6,
.tcc-final, .tcc-ingles, .titulo_espanol, .titulo_ingles, .VV, .IA, .romanos, .arabigos,
.autor_final_2apellidos, .AUT-DOS-NOMBRES, .adscripcion, .nota-de-autor-final, .pais, .ORCID2,
p.identificador, p.identificadorfinal, p.notas_iniciales, p.DOI,
h6.como_citar {
    text-align: left !important;
}

h6.como_citar {
    margin-top: 1.6em;
    margin-bottom: 0.4em;
    font-family: Garamond, 'EB Garamond', 'Times New Roman', serif;
    font-size: 1.05em;
    font-variant: small-caps;
    font-weight: normal;
    text-indent: 0 !important;
    margin-left: 0 !important;
}

[class*="TRANSCRIPCI"], [class*="Transcripci"], [class*="transcripci"], blockquote, p.trun {
    font-size: 1em !important;
    line-height: 1.5 !important;
    margin-top: 1.2em !important;
    margin-bottom: 1.2em !important;
    margin-left: 2.5em !important;
    margin-right: 2.5em !important;
    text-align: justify !important;
    text-indent: 0 !important; 
}

img {
    max-width: 100%;
    height: auto;
    margin-left: 0 !important;
    margin-right: auto !important;
    display: block;
    margin-top: 1.4em;
    margin-bottom: 1.4em;
}

p:has(img), .image-block, figure {
    margin-top: 1.4em !important;
    margin-bottom: 1.4em !important;
}

p.pp:has(img), p.body_text:has(img) {
    text-align: left !important;
}

table {
    margin-top: 1.4em !important;
    margin-bottom: 1.4em !important;
}

.titulo-tabla-imagen {
    display: block !important;
    text-indent: 1.5em !important;
    margin-top: 2.2em !important;
    margin-bottom: 0.5em !important;
    text-align: justify !important;
}

p.pp, p.body_text, p.BODY-text, p.SUMARIO, p.sumario,
.resumenfinal, .abstract_final, .resumen, .resumen_ingles, .palabrasclave, .palabras-clave, .keywords_final, .keywords,
p.bib, p.referencias, p.recepcion, p.aceptacion-publicacion, p.acerca-del-autor, p.publicacion {
    text-align: justify !important;
    text-align-last: left !important;
    hyphens: auto;
    -webkit-hyphens: auto;
}

.table-responsive {
    width: 100%;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    margin: 1.5em 0;
}

table {
    width: 100% !important;
    max-width: 100%;
    margin: 0 !important;
    border-collapse: collapse !important;
    table-layout: auto !important;
}

table col, table colgroup {
    width: auto !important;
}

table td, table th {
    width: auto !important;
    font-family: Garamond, 'EB Garamond', 'Times New Roman', serif !important;
    font-size: 1em !important;
    text-align: justify !important;
    padding: 0.6em !important;
    white-space: normal !important;
    word-break: normal !important;
}

table p, table span, table div {
    font-family: Garamond, 'EB Garamond', 'Times New Roman', serif !important;
    font-size: 1em !important; 
    text-align: justify !important;
    white-space: normal !important;
    line-height: 1.4 !important;
    margin-top: 0 !important;
    margin-bottom: 0 !important;
    text-indent: 0 !important; 
}

.ORCID2 ._idSVGInline, .ORCID ._idSVGInline {
    display: inline-block;
    width: 1em;
    height: 1em;
}
.ORCID2 svg, .ORCID svg {
    width: 100%;
    height: 100%;
    display: block;
}
.ORCID2 a, .ORCID a {
    font-family: Garamond, serif;
}
.ORCID2, .ORCID {
    margin-bottom: 0.2em !important;
    margin-top: 1.2em !important;
}

p.autor_final_2apellidos, p.AUT-DOS-NOMBRES, p.AUT {
    margin-top: 1.2em !important;
    margin-bottom: 0.2em !important;
    font-size: 1.05em !important;
    font-variant: small-caps;
    font-weight: bold;
}

p.adscripcion, p.nota-de-autor-final {
    margin-top: 0 !important;
    margin-bottom: 0.35em !important;
    font-size: 0.95em !important;
    line-height: 1.35 !important;
}

p.pais {
    margin-top: 0 !important;
    margin-bottom: 1.2em !important;
    font-size: 0.95em !important;
}

p.pais + p.autor_final_2apellidos, p.adscripcion + p.autor_final_2apellidos,
p.pais + p.AUT-DOS-NOMBRES, p.nota-de-autor-final + p.AUT-DOS-NOMBRES {
    margin-top: 1.2em !important;
}

p.autor_final_2apellidos + p.resumenfinal, p.adscripcion + p.resumenfinal, p.pais + p.resumenfinal,
p.AUT-DOS-NOMBRES + p.resumen, p.nota-de-autor-final + p.resumen, p.pais + p.resumen {
    margin-top: 1.2em !important;
}

.resumenfinal, .resumen {
    margin-top: 1.2em !important;
}

.tcc-final, h1.titulo_espanol {
    font-family: Garamond, 'EB Garamond', 'Times New Roman', serif;
    font-size: 2em !important;
    font-weight: bold !important;
    line-height: 1.22 !important;
    margin: 0.8em 0 0.15em 0;
}

.tcc-ingles, h2.titulo_ingles {
    font-family: Garamond, 'EB Garamond', 'Times New Roman', serif;
    font-size: 1.25em !important;
    font-style: italic;
    font-weight: normal;
    line-height: 1.2;
    margin: 0 0 1.4em 0;
}

h3.VV, h3.romanos {
    font-size: 1.35em !important;
    margin-top: 1.9em;
    margin-bottom: 1em;
}

h4.IA, h4.arabigos {
    font-size: 1.2em !important;
    margin-top: 1.2em;
    margin-bottom: 0.8em;
}

.ORCID2 + p, .ORCID2 + p + p {
    margin-top: 0 !important;
    margin-bottom: 0 !important;
    line-height: 1.4;
}

ol._idFootAndEndNoteOLAttrs, ol._listStyleNone {
    margin-left: 0 !important;
    padding-left: 0 !important;
    list-style-type: none;
    text-align: justify !important;
}
section._idFootnotes {
    margin-top: 2em;
    border-top: 1px solid #ccc;
    padding-top: 1em;
    text-align: justify !important;
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

.Marco-de-texto-b-sico p.body_text2 span {
    font-size: 1em !important;
    font-family: inherit !important;
    letter-spacing: normal !important;
}

.Marco-de-texto-b-sico p.body_text2.tipo-no-articulo {
    font-size: 1.35em; 
}

p.notas_iniciales {
    color: #58595b;
    font-family: Garamond, serif;
    font-size: 1em;
    line-height: 1.6;
    margin-bottom: 2em;
}

span.NOTA, span.NUMERO-NOTA, span._idGenCharOverride-1, span._idGenCharOverride-2 {
    font-size: 0.85em;
}

p.notas_final {
    color: #000000;
    font-family: Garamond, serif;
    font-size: 0.9em;
    line-height: 1.45;
    margin: 0;
}

p.notas_iniciales a, p.notas_iniciales span.hipervinculo, span.Hiperv-nculo,
p.notas_final a, p.notas_final span.hipervinculo,
.como_citar_section a, .como_citar_section span.hipervinculo,
p.APA a, p.APA span.hipervinculo,
p.iijunam a, p.iijunam span.hipervinculo {
    color: #215e9e;
    text-decoration: underline;
}

.como_citar_section {
    margin-top: 1em;
    margin-bottom: 0.5em;
}
a {
    color: #215e9e;
    text-decoration: none;
    overflow-wrap: break-word;
    word-break: break-word;
}
a:hover {
    text-decoration: underline;
}

hr.HorizontalRule-1 {
    border: none;
    border-top: 1px solid #999;
    margin: 2em 0 1em 0;
}

.no-separar {
    white-space: normal !important;
}

span.Versalitas, span.versalita-OT, span.VERSALITAS, span.Versallitas {
    font-variant: small-caps;
    text-transform: none;
}
span.cursivas {
    font-style: italic;
    font-weight: normal;
}

.como_citar_section, .como_citar_section p, .como_citar_section div, p.APA, p.iijunam {
    text-align: left !important;
    text-indent: 0 !important;
    margin-left: 0 !important;
}

@media (max-width: 768px) {
    .contenedor {
        padding: 4em 3% 1em 3%;
    }
    .Marco-de-texto-b-sico p.body_text2 {
        font-size: 1.2em;
    }
    .Marco-de-texto-b-sico p.body_text2.tipo-no-articulo {
        font-size: 1.2em;
    }
}
"""

def procesar_y_combinar_css(rutas_css_origen: List[str]) -> str:
    """Devuelve todo el CSS procesado como una única cadena de texto en vez de crear archivos."""
    css_final = []
    
    for ruta_css in rutas_css_origen:
        try:
            with open(ruta_css, "r", encoding="utf-8") as f:
                contenido = f.read()
        except (IOError, UnicodeDecodeError):
            continue
            
        contenido_corregido = corregir_css(contenido)
        css_final.append(contenido_corregido)

    css_referencia = generar_css_referencia()
    css_final.append(css_referencia)

    return "\n".join(css_final)