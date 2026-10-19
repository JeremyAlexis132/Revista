"""
Procesador de CSS para la revista Problema (módulo p).

Toma el idGeneratedStyles.css exportado por InDesign y lo adapta a web
conservando la estructura tipográfica del PDF (títulos centrados, fechas a la
derecha, resúmenes justificados, encabezados centrados en gris, etc.):

  * quita el prefijo "ESTILOS-FINALES_" de los selectores;
  * quita el calificador "p." para que los estilos apliquen aunque la etiqueta
    cambie (h1, h2, h3...);
  * pasa px -> em (cada regla se convierte respecto a su propio font-size);
  * sustituye las familias Avenir/Cambria/Minion/Baskerville por una pila web;
  * descarta reglas de objetos de InDesign (transformaciones, tamaños fijos);
  * agrega al final el CSS de referencia (página, espaciado, enlaces, notas...).

Para cambiar la tipografía basta editar la variable --fuente-texto del CSS de
referencia (generar_css_referencia).
"""

import re
from typing import Dict, List, Optional

_BASE_FONT_PX = 11.0  # tamaño de cuerpo de texto en el InDesign de Problema

_PILA_FUENTE = "var(--fuente-texto)"

_LINE_HEIGHT_MAP: Dict[str, str] = {
    "1.2": "1.4", "1.273": "1.55", "1.65": "1.6", "1.75": "1.6",
}

_PROPS_ESPACIADO = (
    "margin-top", "margin-bottom", "margin-left", "margin-right",
    "padding-top", "padding-bottom", "padding-left", "padding-right",
    "text-indent",
)

_RE_REGLA = re.compile(r"([^{}]+)\{([^{}]*)\}")
_RE_PREFIJO = re.compile(r"ESTILOS[-_]FINALES[-_]", re.IGNORECASE)
_RE_PX = re.compile(r"^(-?\d+(?:\.\d+)?)px$")


def _num(valor: float) -> str:
    texto = f"{valor:.3f}".rstrip("0").rstrip(".")
    return texto if texto not in ("", "-0") else "0"


def _a_em(valor_px: str, base_px: float) -> Optional[str]:
    match = _RE_PX.match(valor_px.strip())
    if not match:
        return None
    px = float(match.group(1))
    return "0" if px == 0 else f"{_num(px / base_px)}em"


def _normalizar_selector(selector: str) -> str:
    selector = _RE_PREFIJO.sub("", selector.strip())
    # "p.Clase" -> ".Clase" (no toca la etiqueta p sola ni nombres como "mp.x")
    selector = re.sub(r"(?<![\w.#-])p\.", ".", selector)
    return re.sub(r"\s+", " ", selector)


def _descartar_regla(selector: str) -> bool:
    return "_idGenObjectAttribute" in selector or "_idSVGInline" in selector


def _parsear_declaraciones(cuerpo: str) -> List[List[str]]:
    declaraciones = []
    for parte in cuerpo.split(";"):
        if ":" not in parte:
            continue
        prop, valor = parte.split(":", 1)
        prop, valor = prop.strip().lower(), valor.strip()
        if prop:
            declaraciones.append([prop, valor])
    return declaraciones


def _convertir_regla(match: re.Match) -> str:
    selector = _normalizar_selector(match.group(1))
    if not selector or _descartar_regla(selector):
        return ""

    declaraciones = _parsear_declaraciones(match.group(2))

    # font-size propio de la regla (para convertir márgenes en em relativos a él)
    base_px = _BASE_FONT_PX
    for prop, valor in declaraciones:
        if prop == "font-size":
            m = _RE_PX.match(valor)
            if m and float(m.group(1)) > 0:
                base_px = float(m.group(1))

    salida: List[str] = []
    for prop, valor in declaraciones:
        if prop in ("page-break-after", "page-break-before", "orphans", "widows"):
            continue

        if prop == "-epub-hyphens":
            salida.append(f"hyphens:{valor}")
            salida.append(f"-webkit-hyphens:{valor}")
            continue

        if prop == "font-family":
            salida.append(f"font-family:{_PILA_FUENTE}")
            continue

        if prop == "font-weight" and valor == "800":
            salida.append("font-weight:700")
            continue

        if prop == "font-size":
            convertido = _a_em(valor, _BASE_FONT_PX)
            salida.append(f"font-size:{convertido or valor}")
            continue

        if prop == "line-height":
            salida.append(f"line-height:{_LINE_HEIGHT_MAP.get(valor, valor)}")
            continue

        if prop == "text-align-last" and valor == "justify":
            # Última línea justificada forzada: se ve mal en pantalla
            salida.append("text-align-last:left")
            continue

        if prop in _PROPS_ESPACIADO:
            convertido = _a_em(valor, base_px)
            if convertido is None:
                salida.append(f"{prop}:{valor}")
                continue
            # Sangrías enormes (epígrafes) no caben en móvil: se limitan a un %
            if prop in ("margin-left", "margin-right") and convertido != "0":
                if float(convertido[:-2]) > 6:
                    convertido = f"min({convertido},30%)"
            salida.append(f"{prop}:{convertido}")
            continue

        salida.append(f"{prop}:{valor}")

    if not salida:
        return ""
    cuerpo = ";\n\t".join(salida)
    return f"{selector} {{\n\t{cuerpo};\n}}\n"


def corregir_css(contenido_css: str) -> str:
    """Adapta el CSS de InDesign de Problema a web (ver docstring del módulo)."""
    sin_comentarios = re.sub(r"/\*.*?\*/", "", contenido_css, flags=re.DOTALL)
    return _RE_REGLA.sub(_convertir_regla, sin_comentarios)


def generar_css_base() -> str:
    """
    Estilos de respaldo para las clases de carácter más comunes. Se colocan ANTES del
    CSS de InDesign del artículo, así que si el artículo las define, las suyas ganan;
    si no (cada exportación solo trae los estilos que usa), el aspecto sigue siendo correcto.
    """
    return """/* ---------- Estilos de respaldo (los del artículo tienen prioridad) ---------- */
.grises-vv, .BOLD-ITALIC, .bold-grises-redondas {
    color: #706f6f;
    font-weight: 700;
}
.bold-grises-italicas {
    color: #706f6f;
    font-style: italic;
}
.medium-gris-avenir {
    color: #706f6f;
}
.cursivas {
    font-style: italic;
}
.super-ndice {
    vertical-align: super;
}
"""


def generar_css_referencia() -> str:
    return """/* ============================================
   CSS adicional — Problema (formato tipo documento PDF)
   ============================================ */

:root {
    --fuente-texto: "Avenir Next", "Avenir", "Helvetica Neue", Helvetica, Arial, sans-serif;
    --gris: #706f6f;
    --azul-citar: #0b3a6b;
    --enlace: #1f56a0;
}

html {
    -webkit-text-size-adjust: 100%;
}

body {
    background: #ffffff;
    color: #000000;
    font-family: var(--fuente-texto);
}

/* Página: columna centrada, como una hoja de PDF */
.contenedor {
    box-sizing: border-box;
    width: 100%;
    max-width: none;
    margin: 0 auto;
    padding: 2.5em 5% 3em 5%;
    font-family: var(--fuente-texto);
    font-size: clamp(17px, 0.9vw + 10px, 22px);
    line-height: 1.55;
    color: #000000;
    overflow-wrap: break-word;
    word-wrap: break-word;
}

#_idContainer002 {
    display: block;
    width: 100%;
}

/* ---------- Títulos ---------- */
.contenedor h1.TCC-1 {
    font-size: 1.5em;
    line-height: 1.25;
    margin: 1.2em 0 0.5em 0;
    color: var(--gris);
    font-weight: 700;
    text-align: center;
    text-align-last: center;
    text-indent: 0;
}
.contenedor h2.TCC-2 {
    font-size: 1.15em;
    line-height: 1.3;
    margin: 0 0 1.8em 0;
    color: var(--gris);
    font-style: italic;
    font-weight: 400;
    text-align: center;
    text-align-last: center;
    text-indent: 0;
}

/* Título que InDesign exportó como párrafo normal (p. ej. reseñas: referencia del libro).
   Se ve como título (centrado, gris, negritas) y conserva las cursivas del título del libro. */
.contenedor h1.titulo_referencia,
.contenedor h1.titulo_referencia span {
    color: var(--gris);
    font-weight: 700;
}
.contenedor h1.titulo_referencia {
    font-size: 1.3em;
    line-height: 1.4;
    text-align: center;
    text-align-last: center;
    text-indent: 0;
    text-transform: none;
}
.contenedor h1.titulo_referencia .cursivas,
.contenedor h2.titulo_referencia .cursivas {
    font-style: italic;
}
.contenedor h2.titulo_referencia,
.contenedor h2.titulo_referencia span {
    color: var(--gris);
    font-style: italic;
    font-weight: 400;
}

/* ---------- Autor, ORCID y adscripción ---------- */
.contenedor .autor {
    margin-top: 1.4em;
    margin-bottom: 0.4em;
}
.contenedor p.AUT {
    font-size: 1.1em;
    color: #000000;
    text-align: center;
    text-align-last: center;
    text-indent: 0;
    margin-left: 0;
    margin-right: 0;
}
.contenedor p.orcid {
    font-size: 0.9em;
    margin-top: 0.6em;
    margin-bottom: 0.3em;
    margin-left: 0;
    margin-right: 0;
    text-align: center;
    text-align-last: center;
    text-indent: 0;
}
.contenedor a.orcid-icono {
    display: inline-block;
    width: 1.2em;
    height: 1.2em;
    margin-right: 0.35em;
    vertical-align: -0.25em;
    text-decoration: none;
}
.contenedor a.orcid-icono svg {
    display: block;
    width: 100%;
    height: 100%;
}
.contenedor p.adscripcion_mail {
    font-size: 0.9em;
    margin-top: 0.15em;
    margin-left: 0;
    margin-right: 0;
    text-align: center;
    text-align-last: center;
    text-indent: 0;
}

/* ---------- Fechas (derecha) y DOI (izquierda) ---------- */
.contenedor .fechas {
    margin-top: 1.8em;
    margin-bottom: 0.4em;
}
.contenedor .fechas p {
    font-size: 1em;
    margin-left: 0 !important;
    margin-right: 0 !important;
    text-indent: 0 !important;
    text-align: right !important;
    text-align-last: right !important;
}
.contenedor p.DOI {
    font-size: 0.95em;
    margin-left: 0;
    text-indent: 0;
    text-align: left;
    text-align-last: left;
    margin-top: 0.8em;
    margin-bottom: 1.2em;
}

/* ---------- Bloque inicial: línea en blanco entre bloques ----------
   Resumen + Palabras clave | línea en blanco | Abstract + Keywords | línea en blanco | Sumario */
.contenedor p.resumen, .contenedor p.palabras-clave, .contenedor p.resumen_seg,
.contenedor p.resumen_ingles, .contenedor p.keywords, .contenedor p.SUMARIO {
    font-size: 1em;
    line-height: 1.55;
}
/* Párrafos adicionales del resumen/abstract: pegados al anterior */
.contenedor p.resumen_seg {
    margin-top: 0.35em;
    margin-bottom: 0;
    margin-left: 0;
    text-indent: 0;
    text-align: justify;
    text-align-last: left;
}
.contenedor p.resumen, .contenedor p.palabras-clave,
.contenedor p.resumen_ingles, .contenedor p.keywords {
    margin-left: 0 !important;
    margin-right: 0 !important;
    text-indent: 0 !important;
    text-align: justify !important;
    text-align-last: left !important;
}
.contenedor p.resumen {
    margin-top: 1.2em;
    margin-bottom: 0;
}
.contenedor p.palabras-clave {
    margin-top: 0;
    margin-bottom: 0;
}
.contenedor p.resumen_ingles {
    margin-top: 1.8em;
    margin-bottom: 0;
}
.contenedor p.keywords {
    margin-top: 0;
    margin-bottom: 1.8em;
}
.contenedor p.SUMARIO {
    margin: 1.8em 2em 2.4em 2em;
    text-indent: 0;
    text-align: justify;
    text-align-last: center;
}

/* ---------- Cuerpo ---------- */
.contenedor h3.VV {
    font-size: 1.2em;
    margin: 2.2em 0 0.9em 0;
    color: var(--gris);
    font-weight: 700;
    text-align: center;
    text-align-last: center;
    text-indent: 0;
}
.contenedor h4.IA {
    font-size: 1.1em;
    margin-top: 1.6em;
    margin-bottom: 0.7em;
    text-align: left;
}
.contenedor h5.IS {
    font-size: 1em;
    font-style: italic;
    margin-top: 1.3em;
    margin-bottom: 0.6em;
    text-align: left;
}
.contenedor h4.IA *, .contenedor h5.IS * {
    color: var(--gris);
}

/* Citas en bloque (trun, trp, tri, trpu...): sangradas de ambos lados, letra un poco menor.
   Los párrafos consecutivos de una misma cita van pegados. */
.contenedor p.cita_bloque {
    margin: 1em 2.5em;
    font-size: 0.92em;
    line-height: 1.5;
    text-align: justify;
    text-align-last: left;
    text-indent: 0;
}
.contenedor p.cita_bloque + p.cita_bloque {
    margin-top: 0;
}

/* Epígrafe (cita inicial antes del primer encabezado): bloque a la derecha,
   texto justificado y fuente alineada a la derecha en su propia línea */
.contenedor .epigrafe {
    width: fit-content;
    max-width: min(55%, 34em);
    margin: 1.2em 0 2.2em auto;
}
.contenedor .epigrafe p {
    margin: 0;
    font-size: 0.9em;
    line-height: 1.45;
    text-indent: 0;
    text-align: justify;
    text-align-last: left;
}
.contenedor .epigrafe p * {
    font-size: inherit;
}
.contenedor .epigrafe p.epigrafe_fuente {
    margin-top: 0.35em;
    text-align: right;
    text-align-last: right;
}

/* Referencias: sangría francesa (viene del InDesign), un poco de aire entre entradas */
.contenedor p.bib {
    margin-top: 0.4em;
}

/* ---------- Enlaces ---------- */
.contenedor a,
.contenedor a span {
    color: var(--enlace);
    text-decoration: underline;
}

/* ---------- Figuras y tablas ---------- */
.contenedor p.figura {
    text-align: center;
    text-align-last: center;
    text-indent: 0;
    margin: 0.6em 0;
}
.contenedor p.figura img {
    display: inline-block;
    max-width: 80%;
    height: auto;
}
.contenedor p.titulo_figura {
    text-align: center;
    text-align-last: center;
    text-indent: 0;
    margin-top: 1.6em;
    margin-bottom: 0.4em;
}
.contenedor p.fuente_figura {
    text-align: center;
    text-align-last: center;
    text-indent: 0;
    font-size: 0.85em;
    margin-top: 0.2em;
    margin-bottom: 1.6em;
}

.table-responsive {
    width: 100%;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    margin: 1.4em 0;
}
.contenedor table {
    width: 100%;
    border-collapse: collapse;
}
.contenedor table td, .contenedor table th {
    font-size: 0.9em;
    padding: 0.5em;
    border: 1px solid #bbbbbb;
}

/* ---------- Cómo citar ---------- */
.contenedor .como_citar_section {
    margin-top: 3em;
    margin-bottom: 2em;
}
.contenedor .como_citar_section p {
    text-indent: 0;
    margin-left: 0;
}
.contenedor p.como_citar {
    text-align: center;
    font-weight: bold;
    font-style: italic;
    font-size: 1.1em;
    color: var(--azul-citar);
    margin-top: 0;
    margin-bottom: 1.4em;
}
.contenedor p.iijunam, .contenedor p.APA {
    text-align: left;
    font-size: 1.05em;
    color: var(--azul-citar);
    margin-top: 1.4em;
    margin-bottom: 0.2em;
}
.contenedor p.cita {
    text-align: left;
    text-align-last: left;
    font-size: 1.05em;
    margin-top: 0;
}

/* ---------- Notas al pie ---------- */
.contenedor section._idFootnotes {
    margin-top: 2.5em;
    padding-top: 1em;
    border-top: 1px solid #bbbbbb;
}
.contenedor section._idFootnotes ol._listStyleNone {
    list-style: none;
    margin: 0;
    padding: 0;
}
.contenedor section._idFootnotes li {
    margin: 0.3em 0;
}
.contenedor section._idFootnotes p {
    margin-top: 0;
    font-size: 0.85em;
}

/* ---------- Móvil ---------- */
@media (max-width: 640px) {
    .contenedor {
        font-size: 17px;
        padding: 1.5em 4% 2em 4%;
    }
    .contenedor h1.TCC-1 { font-size: 1.3em; }
    .contenedor .epigrafe { max-width: 88%; }
    .contenedor p.cita_bloque { margin-left: 1.2em; margin-right: 1.2em; }
}

/* ---------- Impresión ---------- */
@media print {
    .contenedor {
        max-width: none;
        padding: 0;
        font-size: 11pt;
    }
    .contenedor a, .contenedor a span {
        color: #000000;
        text-decoration: none;
    }
    .contenedor h3.VV {
        break-after: avoid;
    }
}
"""


def procesar_y_combinar_css(rutas_css_origen: List[str]) -> str:
    css_final = [generar_css_base()]
    for ruta_css in rutas_css_origen:
        try:
            with open(ruta_css, "r", encoding="utf-8") as f:
                css_final.append(corregir_css(f.read()))
        except (IOError, UnicodeDecodeError):
            continue
    css_final.append(generar_css_referencia())
    return "\n".join(css_final)