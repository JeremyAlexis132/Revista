"""
Módulo para procesar y corregir archivos CSS de revistas académicas.
"""

import os
import re
import shutil
from typing import List, Dict

_BASE_FONT_PX = 12.0

_FONT_SIZE_MAP: Dict[str, str] = {
    "5px": "0.55em",
    "9px": "0.9em",
    "10px": "1.1em",
    "12px": "1.3em",
}

_MARGIN_MAP: Dict[str, str] = {
    "0": "0",
    "2px": "0.2em",
    "4px": "0.4em",
    "5px": "0.6em",
    "7px": "0.8em",
    "12px": "1.3em",
    "14px": "1.6em",
    "18px": "2.0em",
    "24px": "2.7em",
    "28px": "3.1em",
    "36px": "4.0em",
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
   CSS adicional — Formato de referencia RMDE
   (https://revistas.juridicas.unam.mx)
   ============================================ */

/* Contenedor principal responsivo */
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

/* ============================================
   ALINEACIÓN A LA IZQUIERDA (Títulos y Metadatos)
   ============================================ */
h1, h2, h3, h4, h5, h6,
.tcc-final, .tcc-ingles, .VV, .IA,
.autor_final_2apellidos, .adscripcion, .pais, .ORCID2,
p.identificador, p.identificadorfinal, p.notas_iniciales,
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

/* Imágenes responsivas y a la izquierda */
img {
    max-width: 100%;
    height: auto;
    margin-left: 0 !important;
    margin-right: auto !important;
    display: block;
    margin-top: 1.4em;
    margin-bottom: 1.4em;
}

/* Dar aire a bloques con imágenes */
p:has(img), .image-block, figure {
    margin-top: 1.4em !important;
    margin-bottom: 1.4em !important;
}

/* Resetear alineación de párrafos que solo contienen imágenes */
p.pp:has(img), p.body_text:has(img) {
    text-align: left !important;
}

table {
    margin-top: 1.4em !important;
    margin-bottom: 1.4em !important;
}

/* Identificadores inyectados para títulos de tablas e imágenes */
.titulo-tabla-imagen {
    display: block !important;
    text-indent: 1.5em !important;
    margin-top: 2.2em !important;
    margin-bottom: 0.5em !important;
    text-align: justify !important;
}

/* ============================================
   FORZAR JUSTIFICADO EN TEXTOS BASE (Restaurado)
   ============================================ */
p.pp, p.body_text, 
.resumenfinal, .abstract_final, .palabrasclave, .keywords_final, 
p.bib, p.recepcion, p.acerca-del-autor, p.publicacion {
    text-align: justify !important;
    text-align-last: left !important;
    hyphens: auto;
    -webkit-hyphens: auto;
}

/* ============================================
   TABLAS (Formato unificado, mismo tamaño, justificadas)
   ============================================ */
.table-responsive {
    width: 100%;
    overflow-x: auto; /* Permite scroll horizontal fluido en móviles */
    -webkit-overflow-scrolling: touch;
    margin: 1.5em 0;
}

table {
    width: 100% !important;
    max-width: 100%;
    margin: 0 !important;
    border-collapse: collapse !important;
    table-layout: auto !important; /* Libera el ancho apachurrado en PC */
}

/* Eliminar anchos fijos de columnas que rompen la vista en PC */
table col, table colgroup {
    width: auto !important;
}

table td, table th {
    width: auto !important;
    font-family: Garamond, 'EB Garamond', 'Times New Roman', serif !important;
    font-size: 1em !important; /* Mismo tamaño de letra que el texto base */
    text-align: justify !important; /* Celdas justificadas */
    padding: 0.6em !important;
    white-space: normal !important;
    word-break: normal !important;
}

/* Forzar estilos a cualquier elemento dentro de la tabla */
table p, table span, table div {
    font-family: Garamond, 'EB Garamond', 'Times New Roman', serif !important;
    font-size: 1em !important; 
    text-align: justify !important; /* Textos justificados */
    white-space: normal !important;
    line-height: 1.4 !important;
    margin-top: 0 !important;
    margin-bottom: 0 !important;
    text-indent: 0 !important; /* Elimina la sangría dentro de la celda */
}

/* ============================================
   OTROS ELEMENTOS Y REFERENCIAS
   ============================================ */
.ORCID2 ._idSVGInline {
    display: inline-block;
    width: 1em;
    height: 1em;
}
.ORCID2 svg {
    width: 100%;
    height: 100%;
    display: block;
}
.ORCID2 a {
    font-family: Garamond, serif;
}
.ORCID2 {
    margin-bottom: 0.2em !important;
    margin-top: 1.2em !important;
}

p.autor_final_2apellidos {
    margin-top: 1.2em !important;
    margin-bottom: 0.2em !important;
    font-size: 1.05em !important;
    font-variant: small-caps;
    font-weight: bold;
}

p.adscripcion {
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

p.pais + p.autor_final_2apellidos {
    margin-top: 1.2em !important;
}

p.adscripcion + p.autor_final_2apellidos {
    margin-top: 1.2em !important;
}

p.autor_final_2apellidos + p.resumenfinal,
p.adscripcion + p.resumenfinal,
p.pais + p.resumenfinal {
    margin-top: 1.2em !important;
}

.resumenfinal {
    margin-top: 1.2em !important;
}

.tcc-final {
    font-family: Garamond, 'EB Garamond', 'Times New Roman', serif;
    font-size: 2em !important;
    font-weight: bold !important;
    line-height: 1.22 !important;
    margin: 0.8em 0 0.15em 0;
}

.tcc-ingles {
    font-family: Garamond, 'EB Garamond', 'Times New Roman', serif;
    font-size: 1.25em !important;
    font-style: italic;
    font-weight: normal;
    line-height: 1.2;
    margin: 0 0 1.4em 0;
}

h3.VV {
    font-size: 1.35em !important;
    margin-top: 1.9em;
    margin-bottom: 1em;
}

h4.IA {
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

/* REGLA AÑADIDA: Fuerza al span a respetar el tamaño grande */
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

p.notas_iniciales a, p.notas_iniciales span.hipervinculo {
    color: #215e9e;
    text-decoration: underline;
}

p.notas_final a, p.notas_final span.hipervinculo,
.como_citar_section a, .como_citar_section span.hipervinculo,
p.APA a, p.APA span.hipervinculo,
p.iijunam a, p.iijunam span.hipervinculo,
p.rmde a, p.rmde span.hipervinculo {
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
span.hipervinculo, span.Hiperv-nculo {
    color: #215e9e;
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

/* Referencias Finales a la izquierda estricto (Como citar) */
.como_citar_section, .como_citar_section p, .como_citar_section div, p.APA, p.iijunam, p.rmde {
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

def procesar_css(
    rutas_css_origen: List[str],
    carpeta_css_destino: str,
    _nombre_revista: str,
) -> List[str]:
    archivos_generados: List[str] = []

    for ruta_css in rutas_css_origen:
        nombre_archivo = os.path.basename(ruta_css)
        try:
            with open(ruta_css, "r", encoding="utf-8") as f:
                contenido = f.read()
        except (IOError, UnicodeDecodeError):
            continue

        contenido_corregido = corregir_css(contenido)
        destino = os.path.join(carpeta_css_destino, nombre_archivo)

        with open(destino, "w", encoding="utf-8") as f:
            f.write(contenido_corregido)

        archivos_generados.append(nombre_archivo)

    css_referencia = generar_css_referencia()
    ruta_referencia = os.path.join(carpeta_css_destino, "referencia.css")
    with open(ruta_referencia, "w", encoding="utf-8") as f:
        f.write(css_referencia)

    archivos_generados.append("referencia.css")
    return archivos_generados