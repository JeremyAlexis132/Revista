"""
Módulo para procesar y corregir archivos CSS específicos de CC.
Unifica la tipografía a Times New Roman, homogeneiza tamaños,
y neutraliza enlaces internos (como los del Sumario).
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
    # Algunos artículos exportan estilos como ".ESTILOS-FINALES_BODY-text"; el HTML
    # procesado usa los nombres sin prefijo, así que se igualan aquí también.
    css = re.sub(r'\.ESTILOS[-_]FINALES[-_]', '.', css, flags=re.IGNORECASE)
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
   CSS adicional — Formato visual unificado CC (Times New Roman)
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
    font-size: 18px; /* Subimos un punto la base general */
    line-height: 1.6;
    word-wrap: break-word;
}

.grises-vv, .bold-grises-redondas, .bold-grises-italicas, .BOLD-ITALIC,
strong.grises-vv, strong.bold-grises-redondas, span.bold-grises-italicas, strong.BOLD-ITALIC,
h2.titulo_ingles, h2.titulo_ingles *,
h3.romanos, h3.romanos *, p[class*="romanos"], p[class*="romanos"] *,
h4.arabigos, h4.arabigos *, p[class*="arabigos"], p[class*="arabigos"] *,
h5.subarabigos, h5.subarabigos *, p[class*="subarabigos"], p[class*="subarabigos"] *,
p.resumen *, p.resumen_ingles *, p.palabras-clave *, p.keywords *, p.SUMARIO *, p[class*="sumario"] * {
    font-weight: normal !important;
    color: #000000 !important;
    font-family: 'Times New Roman', Times, serif !important;
}

h1.titulo_espanol, h2.titulo_ingles, h3.romanos, h4.arabigos, h5.subarabigos,
p[class*="romanos"], p[class*="arabigos"], p[class*="subarabigos"],
p.AUT, p.AUT-DOS-NOMBRES, p.ORCID, p.nota-de-autor-final, p.correo, p.adscripcion,
p.recepcion, p.aceptacion-publicacion, p.DOI, p.como_citar, p.iijunam, p.APA, p.notas_iniciales {
    text-align: left !important;
    text-indent: 0 !important;
    font-family: 'Times New Roman', Times, serif !important;
}

p.notas_iniciales {
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

h1.titulo_espanol {
    font-size: 1.7em !important;
    font-weight: bold !important;
    line-height: 1.22 !important;
    margin: 0.8em 0 0.15em 0 !important;
    -webkit-hyphens: none !important;
    hyphens: none !important;
}

h1.titulo_espanol strong, h1.titulo_espanol span {
    font-family: inherit !important;
    font-size: 1em !important;
    font-weight: bold !important;
    margin: 0 !important;
}

h2.titulo_ingles {
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

h1.titulo_espanol {
    font-size: 1.46625em !important;
}

h2.titulo_ingles {
    font-size: 1.078125em !important;
}

h3.romanos, p[class*="romanos"] {
    font-size: 1.35em !important; 
    margin-top: 1.6em !important;
    margin-bottom: 0.8em !important;
}

h4.arabigos, p[class*="arabigos"]:not([class*="sub"]) {
    font-size: 1.25em !important;
    margin-top: 1.2em !important;
    margin-bottom: 0.8em !important;
}

h5.subarabigos, p[class*="subarabigos"] {
    font-size: 1.15em !important;
    margin-top: 1em !important;
    margin-bottom: 0.6em !important;
    line-height: 1.3 !important;
}

p.AUT, p.AUT-DOS-NOMBRES {
    font-size: 1.2em !important;
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

p.nota-de-autor-final, p.correo, p.adscripcion {
    margin-top: 0 !important;
    margin-bottom: 0.35em !important;
    font-size: 1em !important;
    line-height: 1.35 !important;
    text-align: left !important;
}

/* =========================================================================
   ELIMINACIÓN DE SANGRÍAS Y UNIFICACIÓN DE TAMAÑO (TEXTO NORMAL Y REFERENCIAS)
   ========================================================================= */
p.resumen, p.resumen_ingles, p.palabras-clave, p.keywords, 
p.BODY-text, p.PP, p.body_text, p.cuerpo_texto,
p.SUMARIO, p[class*="sumario"], p.referencias, p.bib, p[class*="bib"],
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

p.cuerpo_texto {
    font-family: 'Times New Roman', Times, serif !important;
    font-size: 1.1em !important;
    line-height: 1.6 !important;
    text-align: justify !important;
    text-indent: 0 !important;
}

/* ==========================================================
   ESPACIADO DEL BLOQUE INICIAL
   Autor + datos | (línea en blanco) | Resumen + Palabras clave |
   (línea en blanco) | Abstract + Keywords | (línea en blanco) | resto
   ========================================================== */
p.resumen {
    margin-top: 1.8em !important;
    margin-bottom: 0 !important;
}
p.palabras-clave {
    margin-top: 0 !important;
    margin-bottom: 0 !important;
}
p.resumen_ingles {
    margin-top: 1.8em !important;
    margin-bottom: 0 !important;
}
p.keywords {
    margin-top: 0 !important;
    margin-bottom: 1.8em !important;
}
/* Sin resumen en español: que el abstract igual se separe del bloque de autor */
p.nota-de-autor-final + p.resumen_ingles {
    margin-top: 1.8em !important;
}

p.recepcion, p.aceptacion-publicacion, p[class*="recibido"] {
    font-family: 'Times New Roman', Times, serif !important;
    text-align: left !important;
    font-size: 1.1em !important;
    line-height: 1.6 !important;
    color: #000;
    margin-left: 0 !important;
    text-indent: 0 !important;
}

/* Párrafos intermedios y final de un bloque de cita: sin separación entre sí */
p.trs, p.trul, p.TRI, p.TRPU, p[class*="trs"], p[class*="trul"] {
    margin-top: 0 !important;
}

/* Listas numeradas: conservar la sangría y escala del documento fuente. */
ol:has(li.nump, li.nums, li.numul) {
    list-style-type: decimal !important;
    padding-left: 0 !important;
    margin-top: 1em !important;
    margin-bottom: 1em !important;
}
ol > li.nump, ol > li.nums, ol > li.numul {
    box-sizing: border-box;
    position: static;
    display: list-item;
    list-style-position: outside !important;
    list-style-type: decimal !important;
    font-size: 1em !important;
    line-height: 1.2 !important;
    margin-left: 1.5em !important;
    margin-right: 0 !important;
    padding-left: 0 !important;
}
ol > li.nump::before, ol > li.nums::before, ol > li.numul::before {
    content: none !important;
}

/* Listas (letrap / letras / letraul): mismo tamaño que cuerpo de texto, numeración decimal */
ol:has(li.letrap, li.letras, li.letraul) {
    list-style-type: decimal !important;
    padding-left: 2em !important;
    margin-top: 1em !important;
    margin-bottom: 1em !important;
}

ul:has(li.rayas, li.nums) {
    list-style: none !important;
    padding-left: 2em !important;
    margin-top: 1em !important;
    margin-bottom: 1em !important;
}

li.rayas, li.nums {
    list-style: none !important;
    position: relative;
}

li.rayas::before, li.nums::before {
    content: "— ";
    position: absolute;
    left: -1.4em;
}

li.rayas, li.nums, li.letrap, li.letras, li.letraul {
    font-family: 'Times New Roman', Times, serif !important;
    font-size: 1.1em !important;
    line-height: 1.6 !important;
    text-align: justify !important;
    list-style-type: decimal !important;
    margin-top: 0.3em !important;
    margin-bottom: 0.3em !important;
    margin-left: 0 !important;
    padding-left: 0 !important;
}

/* Las rayas no llevan numeración: se dibujan con ::before */
li.rayas, li.nums {
    list-style: none !important;
    list-style-type: none !important;
}

p.trun, p.TRP, p.TRI, p.TRPU, p.TRUNIC, p.trs, p.trul,
p[class*="trun"], p[class*="trp"], p[class*="tri"], p[class*="trpu"], p[class*="trunic"], p[class*="trs"], p[class*="trul"] {
    font-family: 'Times New Roman', Times, serif !important;
    margin-left: 2.5em !important;
    margin-right: 2.5em !important;
    font-size: 1.1em !important;
    text-align: justify !important;
    line-height: 1.5 !important;
    margin-top: 1.2em !important;
    margin-bottom: 1.2em !important;
    text-indent: 0 !important; 
}

.contenedor p.TRUN, .contenedor p.TRP, .contenedor p.TRI,
.contenedor p.TRPU, .contenedor p.TRUNIC, .contenedor p.TRS,
.contenedor p.TRUL, .contenedor p.trun, .contenedor p.trs,
.contenedor p.trul {
    font-family: 'Times New Roman', Times, serif !important;
    font-size: 1.1em !important;
    display: block !important;
    clear: both !important;
    width: auto !important;
    box-sizing: border-box !important;
    overflow-wrap: break-word !important;
    white-space: normal !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    text-indent: 0 !important;
    margin-left: 2.5em !important;
    margin-right: 2.5em !important;
    margin-inline-start: 2.5em !important;
    margin-inline-end: 2.5em !important;
    margin-top: 0.8em !important;
    margin-bottom: 0.8em !important;
}

.como_citar_section {
    margin-top: 1em;
    margin-bottom: 0.5em;
}
p.como_citar {
    font-family: 'Times New Roman', Times, serif !important;
    margin-top: 1.6em !important;
    margin-bottom: 0.4em !important;
    font-size: 1.1em !important;
    font-variant: small-caps !important;
    text-align: left !important;
    text-indent: 0 !important;
}

.ORCID ._idSVGInline, ._idSVGInline {
    display: inline-block; width: 1em; height: 1em;
}
.ORCID svg, ._idSVGInline svg {
    width: 100%; height: 100%; display: block;
}

/* ==========================================================
   CONFIGURACIÓN DE ENLACES GLOBALES Y EXCEPCIONES
   ========================================================== */
a, span.Hiperv-nculo, span.hipervinculo {
    color: #215e9e !important;
    text-decoration: underline !important;
}

/* NEUTRALIZACIÓN DE ENLACES EN EL SUMARIO */
p.SUMARIO a, p.SUMARIO span.Hiperv-nculo, p.SUMARIO span.hipervinculo,
.sumario a, .sumario span.Hiperv-nculo, .sumario span.hipervinculo,
p[class*="sumario"] a, p[class*="sumario"] span {
    color: #000000 !important;
    text-decoration: none !important;
    pointer-events: none; /* Deshabilita el clic para que se comporte 100% como texto normal */
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
.Marco-de-texto-b-sico {
    position: absolute; top: 0; left: 0; z-index: 100;
}
.Marco-de-texto-b-sico p.body_text2 {
    background-color: #386abd; color: #ffffff;
    padding: 0.6em 1.2em; font-family: 'Times New Roman', Times, serif !important;
    font-size: 1.35em; font-weight: bold;
    border-radius: 0 4px 4px 0; margin: 0; display: inline-block;
}

/* =========================================================================
   TABLAS RESPONSIVE Y MULTIMEDIA
   ========================================================================= */
img {
    width: 125%; max-width: 125%; height: auto;
    margin: 1.4em 0 !important; display: block;
    text-align: left !important;
}

p.ORCID img, .ORCID img {
    width: auto; max-width: 100%;
    margin: 0 !important;
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
    font-family: 'Times New Roman', Times, serif !important;
    font-size: 1.05em !important;
    text-align: left !important;
    padding: 0.6em !important;
}

p.tit_tabla, p.fuente_tabla, p.encabezado_tabla, p.int_tabla,
table, table p, table td, table th {
    text-align: left !important;
    text-align-last: left !important;
}

@media (max-width: 768px) {
    .contenedor {
        max-width: 100% !important;
        overflow-x: hidden !important;
        padding-left: 3% !important;
        padding-right: 3% !important;
    }
    .contenedor img {
        width: 100% !important;
        max-width: 100% !important;
    }
    h1.titulo_espanol {
        font-size: 1.2em !important;
    }
    h2.titulo_ingles {
        font-size: 1em !important;
    }
    .table-responsive {
        max-width: 100% !important;
    }
    table {
        min-width: 600px !important;
    }
}

/* Notas al pie: más pequeñas que las citas */
p.NOTA-AL-PIE, section._idFootnotes p {
    font-family: 'Times New Roman', Times, serif !important;
    font-size: 0.82em !important;
    line-height: 1.45 !important;
    text-align: justify !important;
    text-align-last: left !important;
    text-indent: 0 !important;
    margin-top: 0.2em !important;
    margin-bottom: 0.2em !important;
}

section._idFootnotes {
    margin-top: 2em;
    border-top: 1px solid #ccc;
    padding-top: 1em;
    text-align: justify !important;
    margin-left: 0 !important;
    padding-left: 0 !important;
}

.contenedor p.cuerpo_texto {
    font-family: 'Times New Roman', Times, serif !important;
    font-size: 1.1em !important;
    line-height: 1.6 !important;
    font-weight: normal !important;
    text-align: justify !important;
    text-indent: 0 !important;
}

.contenedor p.cuerpo_texto * {
    font-family: inherit !important;
    font-size: 1em !important;
    font-weight: inherit !important;
    line-height: inherit !important;
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