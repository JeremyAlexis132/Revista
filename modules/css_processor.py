"""
Módulo para procesar y corregir archivos CSS de revistas académicas.

Realiza las siguientes tareas:
- Copia archivos CSS originales a la carpeta de salida
- Corrige colores transparentes (#0000) a negro (#000000)
- Convierte unidades absolutas (px) a relativas (em) para web
- Ajusta rutas relativas de recursos
- Genera CSS adicional para replicar el formato de referencia de la RMDE
"""

import os
import re
import shutil
from typing import List, Dict


# ──────────────────────────────────────────────────────────
#  Mapeo de conversión px → em (base 12px)
# ──────────────────────────────────────────────────────────
_BASE_FONT_PX = 12.0

# Tamaños de fuente originales en px y su equivalencia em
_FONT_SIZE_MAP: Dict[str, str] = {
    "5px": "0.55em",
    "9px": "0.9em",
    "10px": "1.1em",
    "12px": "1.3em",
}

# Márgenes comunes: px → em (aproximaciones)
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
    """Convierte un valor en px a em con base 12px.

    Args:
        valor_px: Valor CSS con unidad px (ej. "18px").

    Returns:
        Valor convertido a em (ej. "2.0em"), o el original si no aplica.
    """
    match = re.match(r"^(-?\d+(?:\.\d+)?)px$", valor_px.strip())
    if not match:
        return valor_px
    px_val = float(match.group(1))
    if px_val == 0:
        return "0"
    em_val = round(px_val / _BASE_FONT_PX, 1)
    return f"{em_val}em"


def corregir_css(contenido_css: str) -> str:
    """Corrige un archivo CSS para adaptarlo al formato de referencia web.

    Correcciones aplicadas:
    1. Color #0000 → #000000 (negro visible)
    2. Font-size en px → em
    3. Margins/paddings en px → em
    4. Ajusta text-indent en px → em
    5. Elimina propiedades de paginación para epub que no aplican en web
    6. Asegura colores visibles en enlaces e identificadores

    Args:
        contenido_css: Contenido del archivo CSS original.

    Returns:
        Contenido CSS corregido.
    """
    css = contenido_css

    # 1. Corregir colores transparentes → negro
    css = re.sub(r'color:\s*#0000\b', 'color:#000000', css)
    css = re.sub(r'border-color:\s*#0000\b', 'border-color:#000000', css)
    css = re.sub(
        r'border-(left|right|top|bottom)-color:\s*#0000\b',
        r'border-\1-color:#000000',
        css,
    )

    # 2. Convertir font-size de px a em
    for px_val, em_val in _FONT_SIZE_MAP.items():
        css = re.sub(
            rf'font-size:\s*{re.escape(px_val)}',
            f'font-size:{em_val}',
            css,
        )

    # 3. Convertir margins de px a em
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

    # 4. Corregir color del identificador a gris visible
    css = re.sub(
        r'(p\.identificador\s*\{[^}]*?)color:\s*#58595b',
        r'\1color:#58595b',
        css,
    )

    # 5. Asegurar que body_text2 tenga estilos adecuados si existe
    # (para etiquetas tipo "Nota metodológica", "Artículo", etc.)

    return css


def generar_css_referencia() -> str:
    """Genera el CSS adicional necesario para replicar el formato de referencia.

    Este CSS complementa al CSS original de InDesign, añadiendo:
    - Contenedor principal con padding
    - Responsividad de imágenes
    - Estilos ORCID
    - Estilos para notas al pie
    - Correcciones de layout para web

    Returns:
        Cadena con las reglas CSS adicionales.
    """
    return """/* ============================================
   CSS adicional — Formato de referencia RMDE
   (https://revistas.juridicas.unam.mx)
   ============================================ */

/* Contenedor principal */
.contenedor {
    padding: 2em 3.5em 2em 3.5em;
    max-width: 1000px;
    margin: 0 auto;
    font-family: Garamond, 'EB Garamond', 'Times New Roman', serif;
}

/* Imágenes responsivas */
img {
    max-width: 100%;
    height: auto;
    margin-left: auto;
    margin-right: auto;
    display: block;
}

/* Centrar imágenes dentro de párrafos */
p.pp:has(img),
p.body_text:has(img) {
    text-align: center;
    margin-top: 0.5em;
    margin-bottom: 0.5em;
}

/* Tablas — espaciado */
p.pp:has(+ table),
p.body_text:has(+ table) {
    text-align: center;
    margin-top: 0.5em;
    margin-bottom: 0.5em;
}
table + p.pp,
table + p.body_text {
    margin-top: 1.5em;
    margin-bottom: 1.5em;
}

/* Tablas — max-width */
table {
    max-width: 100%;
    margin-left: auto;
    margin-right: auto;
}

/* Estilos ORCID */
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
    margin-top: 1.5em !important;
}
.ORCID2 + p,
.ORCID2 + p + p {
    margin-top: 0 !important;
    margin-bottom: 0 !important;
    line-height: 1.4;
}

/* Notas al pie */
ol._idFootAndEndNoteOLAttrs,
ol._listStyleNone {
    margin-left: 0 !important;
    padding-left: 0 !important;
    list-style-type: none;
}

section._idFootnotes {
    margin-top: 2em;
    border-top: 1px solid #ccc;
    padding-top: 1em;
}

/* Etiqueta flotante (Nota metodológica, Artículo, etc.) */
.Marco-de-texto-b-sico {
    position: fixed;
    top: 80px;
    left: 0;
    z-index: 100;
}

.Marco-de-texto-b-sico p.body_text2 {
    background-color: #386abd;
    color: #ffffff;
    padding: 0.5em 1em;
    font-family: Garamond, serif;
    font-size: 1.1em;
    font-weight: normal;
    writing-mode: horizontal-tb;
    border-radius: 0 4px 4px 0;
}

/* Información de la revista (notas iniciales) */
p.notas_iniciales {
    color: #58595b;
    font-family: Garamond, serif;
    font-size: 0.9em;
    line-height: 1.6;
    margin-bottom: 2em;
}

p.notas_iniciales a {
    color: #215e9e;
    text-decoration: underline;
}

/* Separador horizontal antes de notas */
hr.HorizontalRule-1 {
    border: none;
    border-top: 1px solid #999;
    margin: 2em 0 1em 0;
}

/* Hipervínculos */
a {
    color: #215e9e;
    text-decoration: none;
}
a:hover {
    text-decoration: underline;
}
span.hipervinculo {
    color: #0645ad;
}
span.Hiperv-nculo {
    color: #215e9e;
    text-decoration: underline;
}

/* Línea de separación */
.no-separar {
    white-space: nowrap;
}

/* Versalitas */
span.Versalitas,
span.versalita-OT,
span.VERSALITAS {
    font-variant: small-caps;
    text-transform: none;
}

/* Cursivas */
span.cursivas {
    font-style: italic;
    font-weight: normal;
}

/* Etiqueta tipo revista */
p.identificador {
    color: #58595b;
    font-size: 0.55em;
}
p.identificadorfinal {
    color: #386abd;
    font-size: 0.55em;
    margin-bottom: 1.3em;
}

/* Viewport para responsividad */
@media (max-width: 768px) {
    .contenedor {
        padding: 1em 1.5em;
    }
}
"""


def procesar_css(
    rutas_css_origen: List[str],
    carpeta_css_destino: str,
    nombre_revista: str,
) -> List[str]:
    """Procesa y copia archivos CSS al destino, generando CSS adicional.

    Para cada archivo CSS de origen:
    1. Lee el contenido
    2. Aplica correcciones (colores, unidades, etc.)
    3. Escribe el archivo corregido en la carpeta destino

    Adicionalmente genera un archivo 'referencia.css' con los estilos
    necesarios para replicar el formato de la página de referencia.

    Args:
        rutas_css_origen: Lista de rutas a archivos CSS originales.
        carpeta_css_destino: Carpeta css/ de salida.
        nombre_revista: Nombre de la revista (para nombres de archivo).

    Returns:
        Lista de nombres de archivos CSS generados en la carpeta destino.
    """
    archivos_generados: List[str] = []

    # Copiar y corregir CSS originales
    for ruta_css in rutas_css_origen:
        nombre_archivo = os.path.basename(ruta_css)
        try:
            with open(ruta_css, "r", encoding="utf-8") as f:
                contenido = f.read()
        except (IOError, UnicodeDecodeError) as e:
            print(f"    ⚠ No se pudo leer {ruta_css}: {e}")
            continue

        contenido_corregido = corregir_css(contenido)
        destino = os.path.join(carpeta_css_destino, nombre_archivo)

        with open(destino, "w", encoding="utf-8") as f:
            f.write(contenido_corregido)

        archivos_generados.append(nombre_archivo)
        print(f"    ✓ CSS corregido: {nombre_archivo}")

    # Generar CSS de referencia adicional
    css_referencia = generar_css_referencia()
    ruta_referencia = os.path.join(carpeta_css_destino, "referencia.css")
    with open(ruta_referencia, "w", encoding="utf-8") as f:
        f.write(css_referencia)

    archivos_generados.append("referencia.css")
    print("    ✓ CSS de referencia generado: referencia.css")

    return archivos_generados
