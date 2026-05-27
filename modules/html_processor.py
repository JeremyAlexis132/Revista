"""
Módulo para extraer y reestructurar HTML de revistas académicas.

Funcionalidades principales:
- Extracción de contenido semántico del HTML original de InDesign
- Reestructuración completa del HTML siguiendo el formato de referencia
  de la RMDE (https://revistas.juridicas.unam.mx)
- Generación de HTML limpio con estructura contenedor + CSS de referencia

Utiliza BeautifulSoup4 para parsing del HTML.
"""

import os
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from bs4 import BeautifulSoup, Tag, NavigableString


# ──────────────────────────────────────────────────────────
#  Modelo de datos del artículo
# ──────────────────────────────────────────────────────────

@dataclass
class Autor:
    """Representa un autor del artículo."""
    nombre: str = ""
    orcid: str = ""
    adscripcion: str = ""
    pais: str = ""


@dataclass
class ContenidoArticulo:
    """Contenido extraído de un artículo de revista."""
    # Metadatos
    identificadores: List[str] = field(default_factory=list)
    tipo_articulo: str = ""  # "Nota metodológica", "Artículo", etc.

    # Títulos
    titulo_es: str = ""
    titulo_en: str = ""

    # Autores
    autores: List[Autor] = field(default_factory=list)

    # Resumen y abstract
    resumen: str = ""
    abstract: str = ""
    palabras_clave: str = ""
    keywords: str = ""

    # Cuerpo del artículo (HTML de las secciones)
    secciones_cuerpo: List[str] = field(default_factory=list)

    # Referencias bibliográficas
    referencias: List[str] = field(default_factory=list)

    # Información adicional
    fechas: List[str] = field(default_factory=list)  # recepción, aceptación, publicación
    acerca_autores: List[str] = field(default_factory=list)
    como_citar: List[str] = field(default_factory=list)

    # Notas al pie
    notas_html: str = ""

    # HTML crudo del cuerpo (todo entre keywords y referencias)
    cuerpo_html_crudo: str = ""


# ──────────────────────────────────────────────────────────
#  SVG de ORCID (icono inline)
# ──────────────────────────────────────────────────────────

ORCID_SVG = """<span class="_idSVGInline"><svg version="1.1" xmlns="https://lh7-rt.googleusercontent.com/docsz/AD_4nXfwdGXelHGv7MlGZDMGvyU2eVt42E2zw-ycbLEvUNupHXL3Z0aYtEc3I-N4UdW7pgx6-40X_NoZRG15-rwBd_nnmxPJNxRjl4cV47oLrQ4qPWekGK08Pu6hdms7SHxNAZ0S7Bzq4OP7a85Vr0kz6NuIytSy?key=FVu4pMW4OSNP023W3l6MTA" x="0px" y="0px" viewBox="0 0 256 256" xml:space="preserve">
<style type="text/css">.st0{fill:#A6CE39;}.st1{fill:#FFFFFF;}</style>
<circle class="st0" cx="128" cy="128" r="128"/>
<g>
<path class="st1" d="M86.3,186.2H70.9V79.1h15.4v48.4V186.2z"/>
<path class="st1" d="M108.9,79.1h41.6c39.6,0,57,28.3,57,53.6c0,27.5-21.5,53.6-56.8,53.6h-41.8V79.1z M124.3,172.4h24.5c34.9,0,42.9-26.5,42.9-39.7c0-21.5-13.7-39.7-43.7-39.7h-23.7V172.4z"/>
<path class="st1" d="M88.7,56.8c0,5.5-4.5,10.1-10.1,10.1c-5.6,0-10.1-4.6-10.1-10.1c0-5.6,4.5-10.1,10.1-10.1C84.2,46.7,88.7,51.3,88.7,56.8z"/>
</g></svg></span>"""


# ──────────────────────────────────────────────────────────
#  Extracción de contenido
# ──────────────────────────────────────────────────────────

def _limpiar_texto(elemento) -> str:
    """Extrae texto limpio de un elemento BS4, eliminando spans no-separar."""
    if elemento is None:
        return ""
    return elemento.get_text(strip=False).strip()


def _obtener_html_interno(elemento) -> str:
    """Obtiene el HTML interno de un elemento, preservando formato."""
    if elemento is None:
        return ""
    return "".join(str(child) for child in elemento.children)


def extraer_contenido(html_path: str) -> ContenidoArticulo:
    """Extrae todo el contenido semántico de un archivo HTML de InDesign.

    Analiza el HTML exportado de InDesign y extrae:
    - Identificadores de la revista
    - Título en español e inglés
    - Autores con ORCID, adscripción y país
    - Resumen y abstract
    - Palabras clave y keywords
    - Secciones del cuerpo del artículo
    - Referencias bibliográficas
    - Fechas y notas sobre los autores
    - Información de cómo citar
    - Notas al pie

    Args:
        html_path: Ruta al archivo HTML de entrada.

    Returns:
        Objeto ContenidoArticulo con toda la información extraída.
    """
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    contenido = ContenidoArticulo()

    # Buscar el contenedor principal
    container = soup.find("div", class_="_idGenObjectStyleOverride-1")
    if container is None:
        container = soup.body
    if container is None:
        print("    ⚠ No se encontró contenedor principal en el HTML")
        return contenido

    # Recopilar todos los elementos hijos directos
    elementos = [e for e in container.children if isinstance(e, Tag)]

    # ── Tipo de artículo (si hay un Marco-de-texto-b-sico) ──
    marco = soup.find("div", class_="Marco-de-texto-b-sico")
    if marco:
        body_text2 = marco.find("p", class_="body_text2")
        if body_text2:
            contenido.tipo_articulo = _limpiar_texto(body_text2)

    # ── Recorrer elementos secuencialmente ──
    idx = 0
    fase = "identificadores"
    autor_actual: Optional[Autor] = None

    while idx < len(elementos):
        elem = elementos[idx]
        clases = " ".join(elem.get("class", []))

        # ── IDENTIFICADORES ──
        if fase == "identificadores" and ("identificador" in clases):
            contenido.identificadores.append(_obtener_html_interno(elem))
            idx += 1
            continue

        # ── TÍTULO ESPAÑOL ──
        if elem.name == "h1" and "tcc-final" in clases:
            contenido.titulo_es = _obtener_html_interno(elem)
            fase = "titulo_en"
            idx += 1
            continue

        # ── TÍTULO INGLÉS ──
        if fase == "titulo_en" and elem.name == "h2" and "tcc-ingles" in clases:
            contenido.titulo_en = _obtener_html_interno(elem)
            fase = "autores"
            idx += 1
            continue

        # ── AUTORES ──
        if "autor_final_2apellidos" in clases:
            if autor_actual is not None:
                contenido.autores.append(autor_actual)
            autor_actual = Autor(nombre=_obtener_html_interno(elem))
            # Buscar ORCID en el siguiente adscripcion
            fase = "autor_detalles"
            idx += 1
            continue

        if fase == "autor_detalles":
            if "adscripcion" in clases:
                texto = _limpiar_texto(elem)
                # Verificar si es un ORCID (contiene orcid.org)
                enlace = elem.find("a")
                if enlace and "orcid.org" in (enlace.get("href", "") or ""):
                    if autor_actual:
                        autor_actual.orcid = enlace.get("href", "")
                else:
                    if autor_actual:
                        if autor_actual.adscripcion:
                            autor_actual.adscripcion += " | " + texto
                        else:
                            autor_actual.adscripcion = texto
                idx += 1
                continue
            elif "pais" in clases:
                if autor_actual:
                    autor_actual.pais = _limpiar_texto(elem)
                idx += 1
                continue
            else:
                # Ya no son detalles de autor
                fase = "resumen"

        # ── RESUMEN ──
        if "resumenfinal" in clases:
            contenido.resumen = _obtener_html_interno(elem)
            fase = "palabras_clave"
            idx += 1
            continue

        # ── PALABRAS CLAVE ──
        if "palabrasclave" in clases:
            contenido.palabras_clave = _obtener_html_interno(elem)
            fase = "abstract"
            idx += 1
            continue

        # ── ABSTRACT ──
        if "abstract_final" in clases:
            contenido.abstract = _obtener_html_interno(elem)
            fase = "keywords"
            idx += 1
            continue

        # ── KEYWORDS ──
        if "keywords_final" in clases:
            contenido.keywords = _obtener_html_interno(elem)
            fase = "cuerpo"
            idx += 1
            continue

        # ── CUERPO DEL ARTÍCULO ──
        if fase == "cuerpo":
            # Detectar inicio de referencias
            if elem.name == "h3" and "VV" in clases:
                texto_h3 = _limpiar_texto(elem).lower()
                if "referencia" in texto_h3:
                    fase = "referencias"
                    contenido.secciones_cuerpo.append(str(elem))
                    idx += 1
                    continue

            # Detectar fechas de recepción (fin del artículo)
            if "recepcion" in clases:
                fase = "postcontenido"
                # No incrementar idx; procesar en la siguiente fase
            else:
                contenido.secciones_cuerpo.append(str(elem))
                idx += 1
                continue

        # ── REFERENCIAS BIBLIOGRÁFICAS ──
        if fase == "referencias":
            if "bib" in clases:
                contenido.referencias.append(str(elem))
                idx += 1
                continue
            elif "recepcion" in clases:
                fase = "postcontenido"
            else:
                # Otro elemento dentro de la sección de referencias
                contenido.referencias.append(str(elem))
                idx += 1
                continue

        # ── POST-CONTENIDO (fechas, autores, cómo citar) ──
        if fase == "postcontenido":
            if "recepcion" in clases:
                contenido.fechas.append(_obtener_html_interno(elem))
            elif "publicacion" in clases:
                contenido.fechas.append(_obtener_html_interno(elem))
            elif "como_citar" in clases:
                contenido.como_citar.append(str(elem))
            elif "acerca-del-autor" in clases:
                # Puede ser fecha de aceptación o info del autor
                texto = _limpiar_texto(elem)
                if texto.startswith("Aceptación:"):
                    contenido.fechas.append(_obtener_html_interno(elem))
                else:
                    contenido.acerca_autores.append(str(elem))
            elif "Estilo-de-p-rrafo-6" in clases:
                contenido.acerca_autores.append(str(elem))
            elif "iijunam" in clases or "APA" in clases:
                contenido.como_citar.append(str(elem))
            idx += 1
            continue

        idx += 1

    # Guardar último autor
    if autor_actual is not None:
        contenido.autores.append(autor_actual)

    # ── NOTAS AL PIE ──
    seccion_notas = soup.find("section", class_="_idFootnotes")
    if seccion_notas:
        contenido.notas_html = str(seccion_notas)

    # Buscar hr antes de las notas
    hr = soup.find("hr", class_="HorizontalRule-1")

    return contenido


# ──────────────────────────────────────────────────────────
#  Corrección de rutas en HTML
# ──────────────────────────────────────────────────────────

def _corregir_rutas_imagenes(html: str) -> str:
    """Reemplaza rutas de imágenes a rutas relativas a images/.

    Convierte rutas como:
      20462_rmde-web-resources/image/Gráfica1_editable.png
    a:
      images/Gráfica1_editable.png

    Args:
        html: Cadena HTML con rutas originales.

    Returns:
        HTML con rutas corregidas.
    """
    # Patrón para rutas de imágenes tipo InDesign
    html = re.sub(
        r'src="[^"]*?(?:web-resources/image/|image/)([^"]+)"',
        r'src="images/\1"',
        html,
    )
    return html


def _corregir_rutas_footnotes(html: str) -> str:
    """Corrige las rutas de los enlaces de notas al pie para que apunten
    al mismo documento (index.html).

    Args:
        html: Cadena HTML con enlaces de notas.

    Returns:
        HTML con enlaces corregidos.
    """
    # Cambiar href="20462_rmde.html#footnote-..." a href="#footnote-..."
    html = re.sub(
        r'href="[^"#]*\.html(#[^"]+)"',
        r'href="\1"',
        html,
    )
    return html


# ──────────────────────────────────────────────────────────
#  Generación del HTML reestructurado
# ──────────────────────────────────────────────────────────

def _generar_bloque_autor(autor: Autor) -> str:
    """Genera el HTML de un autor siguiendo el formato de referencia.

    Args:
        autor: Objeto Autor con la información.

    Returns:
        HTML del bloque del autor.
    """
    lineas = []

    # Nombre con ORCID
    orcid_html = ""
    if autor.orcid:
        orcid_html = (
            f' <span class="Versalitas">'
            f'<a href="{autor.orcid}">{ORCID_SVG}</a>'
            f'</span>'
        )

    lineas.append(
        f'<p class="autor_final_2apellidos ORCID2">'
        f'{autor.nombre}{orcid_html}</p>'
    )

    # Adscripción
    if autor.adscripcion:
        lineas.append(f'<p class="adscripcion">{autor.adscripcion}</p>')

    # País
    if autor.pais:
        lineas.append(f'<p class="pais">{autor.pais}</p>')

    return "\n\t\t\t".join(lineas)


def generar_html_referencia(
    contenido: ContenidoArticulo,
    archivos_css: List[str],
    nombre_revista: str,
) -> str:
    """Genera el HTML completo reestructurado siguiendo el formato de referencia.

    El HTML generado replica la estructura visual de:
    https://revistas.juridicas.unam.mx/index.php/derecho-electoral/article/view/20456/20410

    Estructura:
    - <head> con viewport, charset, CSS links
    - Marco flotante con tipo de artículo
    - Contenedor principal con:
      - Identificadores de la revista
      - Títulos (español e inglés)
      - Autores con ORCID
      - Resumen y abstract
      - Palabras clave y keywords
      - Cuerpo del artículo
      - Referencias bibliográficas
      - Información adicional
      - Notas al pie

    Args:
        contenido: Objeto ContenidoArticulo con datos extraídos.
        archivos_css: Lista de nombres de archivos CSS disponibles.
        nombre_revista: Nombre de la revista (para el título del documento).

    Returns:
        Cadena HTML completa del documento reestructurado.
    """
    # ── CSS links ──
    css_links = []
    for css_file in archivos_css:
        css_links.append(f'\t\t<link href="css/{css_file}" rel="stylesheet" type="text/css" />')
    css_links_str = "\n".join(css_links)

    # ── Identificadores ──
    identificadores_html = ""
    if contenido.identificadores:
        id_lines = []
        for i, ident in enumerate(contenido.identificadores):
            if i < len(contenido.identificadores) - 1:
                id_lines.append(f'<br>{ident}')
            else:
                id_lines.append(f'<br>{ident}<br><br>')
        identificadores_html = f"""
\t\t<p class="notas_iniciales">\t
\t\t\t{''.join(id_lines)}
\t\t</p>"""

    # ── Tipo de artículo (etiqueta flotante) ──
    tipo_articulo = contenido.tipo_articulo or "Artículo"
    marco_html = f"""
\t\t<div id="_idContainer000" class="Marco-de-texto-b-sico _idGenObjectStyleOverride-1">
\t\t\t<p class="body_text2"><span class="CharOverride-1">{tipo_articulo}</span></p>
\t\t</div>"""

    # ── Autores ──
    autores_html = "\n\t\t\t".join(
        _generar_bloque_autor(a) for a in contenido.autores
    )

    # ── Resumen ──
    resumen_html = ""
    if contenido.resumen:
        resumen_html = f'<p class="resumenfinal ParaOverride-5">{contenido.resumen}</p>'

    # ── Palabras clave ──
    palabras_html = ""
    if contenido.palabras_clave:
        palabras_html = f'<p class="palabrasclave">{contenido.palabras_clave}</p>'

    # ── Abstract ──
    abstract_html = ""
    if contenido.abstract:
        abstract_html = f'<p class="abstract_final" lang="en-US">{contenido.abstract}</p>'

    # ── Keywords ──
    keywords_html = ""
    if contenido.keywords:
        keywords_html = f'<p class="keywords_final">{contenido.keywords}</p>'

    # ── Cuerpo ──
    cuerpo_html = "\n\t\t\t".join(contenido.secciones_cuerpo)

    # ── Referencias ──
    referencias_html = "\n\t\t\t".join(contenido.referencias)

    # ── Fechas ──
    fechas_html_parts = []
    for i, fecha in enumerate(contenido.fechas):
        if i == 0:
            fechas_html_parts.append(f'<p class="recepcion">{fecha}</p>')
        elif "Aceptación" in fecha:
            fechas_html_parts.append(f'<p class="acerca-del-autor">{fecha}</p>')
        else:
            fechas_html_parts.append(f'<p class="publicacion">{fecha}</p>')
    fechas_html = "\n\t\t\t".join(fechas_html_parts)

    # ── Acerca de los autores ──
    acerca_html = "\n\t\t\t".join(contenido.acerca_autores)

    # ── Cómo citar ──
    como_citar_html = "\n\t\t\t".join(contenido.como_citar)

    # ── Notas al pie ──
    notas_html = contenido.notas_html if contenido.notas_html else ""

    # ── Separador HR ──
    hr_html = '<hr class="HorizontalRule-1" />' if notas_html else ""

    # ── Ensamblado final ──
    html = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="es-ES">
\t<head>
\t\t<meta charset="utf-8" />
\t\t<meta name="viewport" content="width=device-width, initial-scale=1.0" />
\t\t<title>{nombre_revista}</title>
{css_links_str}
\t</head>
\t<body id="x{nombre_revista}">
{marco_html}
\t\t<div class="contenedor">
{identificadores_html}
\t\t<div id="_idContainer003" class="_idGenObjectStyleOverride-2">
\t\t\t<h1 class="tcc-final">{contenido.titulo_es}</h1>
\t\t\t<h2 class="tcc-ingles" lang="en-US">{contenido.titulo_en}</h2>
\t\t\t{autores_html}
\t\t\t{resumen_html}
\t\t\t{palabras_html}
\t\t\t{abstract_html}
\t\t\t{keywords_html}
\t\t\t{cuerpo_html}
\t\t\t{referencias_html}
\t\t\t{fechas_html}
\t\t\t{acerca_html}
\t\t\t{como_citar_html}
\t\t\t{hr_html}
\t\t\t{notas_html}
\t\t</div>
\t</div>
\t</body>
</html>"""

    # Corregir rutas de imágenes y notas al pie
    html = _corregir_rutas_imagenes(html)
    html = _corregir_rutas_footnotes(html)

    return html


# ──────────────────────────────────────────────────────────
#  Función principal del módulo
# ──────────────────────────────────────────────────────────

def procesar_html(
    html_path: str,
    archivos_css: List[str],
    ruta_salida_html: str,
    nombre_revista: str,
) -> bool:
    """Función principal: extrae contenido y genera HTML reestructurado.

    Args:
        html_path: Ruta al archivo HTML de entrada.
        archivos_css: Lista de archivos CSS a referenciar.
        ruta_salida_html: Ruta donde se escribirá el index.html de salida.
        nombre_revista: Nombre de la revista para metadatos.

    Returns:
        True si el procesamiento fue exitoso, False en caso contrario.
    """
    try:
        print(f"    → Extrayendo contenido de: {os.path.basename(html_path)}")
        contenido = extraer_contenido(html_path)

        print(f"      Título: {_limpiar_texto_simple(contenido.titulo_es)[:80]}...")
        print(f"      Autores: {len(contenido.autores)}")
        print(f"      Secciones: {len(contenido.secciones_cuerpo)}")
        print(f"      Referencias: {len(contenido.referencias)}")

        print(f"    → Generando HTML reestructurado...")
        html_final = generar_html_referencia(contenido, archivos_css, nombre_revista)

        with open(ruta_salida_html, "w", encoding="utf-8") as f:
            f.write(html_final)

        print(f"    ✓ HTML generado: index.html")
        return True

    except Exception as e:
        print(f"    ✗ Error procesando HTML: {e}")
        import traceback
        traceback.print_exc()
        return False


def _limpiar_texto_simple(html_str: str) -> str:
    """Limpia tags HTML y devuelve texto plano."""
    soup = BeautifulSoup(html_str, "html.parser")
    return soup.get_text(strip=True)
