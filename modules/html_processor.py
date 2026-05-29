"""
Módulo para extraer y reestructurar HTML de revistas académicas.
"""

import os
import re
import urllib.parse
import unicodedata
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from bs4 import BeautifulSoup, Tag, NavigableString


# ──────────────────────────────────────────────────────────
#  Modelo de datos del artículo
# ──────────────────────────────────────────────────────────

@dataclass
class Autor:
    nombre: str = ""
    orcid: str = ""
    adscripcion: str = ""
    pais: str = ""

@dataclass
class ContenidoArticulo:
    identificadores: List[str] = field(default_factory=list)
    tipo_articulo: str = ""
    titulo_es: str = ""
    titulo_en: str = ""
    autores: List[Autor] = field(default_factory=list)
    resumen: str = ""
    abstract: str = ""
    palabras_clave: str = ""
    keywords: str = ""
    secciones_cuerpo: List[str] = field(default_factory=list)
    referencias: List[str] = field(default_factory=list)
    fechas: List[str] = field(default_factory=list)
    acerca_autores: List[str] = field(default_factory=list)
    como_citar: List[str] = field(default_factory=list)
    notas_html: str = ""
    cuerpo_html_crudo: str = ""

ORCID_SVG = """<span class="_idSVGInline"><svg version="1.1" xmlns="https://lh7-rt.googleusercontent.com/docsz/AD_4nXfwdGXelHGv7MlGZDMGvyU2eVt42E2zw-ycbLEvUNupHXL3Z0aYtEc3I-N4UdW7pgx6-40X_NoZRG15-rwBd_nnmxPJNxRjl4cV47oLrQ4qPWekGK08Pu6hdms7SHxNAZ0S7Bzq4OP7a85Vr0kz6NuIytSy?key=FVu4pMW4OSNP023W3l6MTA" x="0px" y="0px" viewBox="0 0 256 256" xml:space="preserve">
<style type="text/css">.st0{fill:#A6CE39;}.st1{fill:#FFFFFF;}</style>
<circle class="st0" cx="128" cy="128" r="128"/>
<g>
<path class="st1" d="M86.3,186.2H70.9V79.1h15.4v48.4V186.2z"/>
<path class="st1" d="M108.9,79.1h41.6c39.6,0,57,28.3,57,53.6c0,27.5-21.5,53.6-56.8,53.6h-41.8V79.1z M124.3,172.4h24.5c34.9,0,42.9-26.5,42.9-39.7c0-21.5-13.7-39.7-43.7-39.7h-23.7V172.4z"/>
<path class="st1" d="M88.7,56.8c0,5.5-4.5,10.1-10.1,10.1c-5.6,0-10.1-4.6-10.1-10.1c0-5.6,4.5-10.1,10.1-10.1C84.2,46.7,88.7,51.3,88.7,56.8z"/>
</g></svg></span>"""


def _limpiar_texto(elemento) -> str:
    if elemento is None:
        return ""
    return elemento.get_text(strip=False).strip()

def _obtener_html_interno(elemento) -> str:
    if elemento is None:
        return ""
    return "".join(str(child) for child in elemento.children)


def _normalizar_html_bloque(html: str) -> str:
    html = re.sub(r"\s+", " ", html or "")
    return html.strip()


def _deduplicar_bloques_html(bloques: List[str]) -> List[str]:
    vistos = set()
    bloques_unicos: List[str] = []

    for bloque in bloques:
        clave = _normalizar_html_bloque(bloque)
        if not clave or clave in vistos:
            continue
        vistos.add(clave)
        bloques_unicos.append(bloque)

    return bloques_unicos


def _extraer_tipo_desde_marco(soup: BeautifulSoup) -> str:
    marco = soup.find("div", class_="Marco-de-texto-b-sico")
    if not marco:
        return ""

    body_text2 = marco.find("p", class_="body_text2")
    if body_text2:
        return _limpiar_texto(body_text2)

    partes: List[str] = []
    for p in marco.find_all("p"):
        texto = _limpiar_texto(p)
        if texto:
            partes.append(texto)
    return " ".join(partes).strip()


def _normalizar_tipo_articulo(texto: str) -> str:
    limpio = re.sub(r"\s+", " ", texto or "").strip()
    if not limpio:
        return ""
    clave = limpio.lower().replace(" ", "")
    reemplazos = {
        "observatorioelectoral": "Observatorio electoral",
    }
    if clave in reemplazos:
        return reemplazos[clave]
    return limpio

def _clave_tipo_articulo(texto: str) -> str:
    limpio = unicodedata.normalize("NFKD", texto or "")
    limpio = "".join(ch for ch in limpio if not unicodedata.combining(ch))
    limpio = re.sub(r"\s+", " ", limpio).strip().lower()
    return limpio


def _extraer_orcid_desde_elemento(elemento: Optional[Tag]) -> str:
    if elemento is None:
        return ""

    enlace = elemento.find("a", href=True)
    if enlace and "orcid.org" in enlace["href"]:
        return enlace["href"].strip()

    texto = elemento.get_text(" ", strip=True)
    match = re.search(r"\b\d{4}-\d{4}-\d{4}-\d{3}[\dX]\b", texto)
    if match:
        return f"https://orcid.org/{match.group(0)}"

    return ""


def _limpiar_nombre_autor(elemento: Tag) -> str:
    copia = BeautifulSoup(str(elemento), "html.parser")
    contenedor = copia.find("p") or copia

    for link in contenedor.find_all("a", href=True):
        if "orcid.org" in link["href"]:
            link.decompose()

    for img in contenedor.find_all("img"):
        src = img.get("src", "").lower()
        if "orcid" in src:
            img.decompose()

    return "".join(str(child) for child in contenedor.children).strip()


def _clases_de_elemento(elemento: Tag) -> List[str]:
    clases = elemento.get("class", [])
    if isinstance(clases, str):
        return [clases]
    return [str(c) for c in clases]


def _tiene_orcid_en_bloque(elemento: Tag) -> bool:
    enlace = elemento.find("a", href=True)
    if enlace and "orcid.org" in enlace.get("href", ""):
        return True
    return bool(re.search(r"\b\d{4}-\d{4}-\d{4}-\d{3}[\dX]\b", elemento.get_text(" ", strip=True)))


# --- SOLUCIÓN ACTUALIZADA PARA CAPTURAR A TODOS LOS AUTORES ---
def _parece_bloque_autor(elemento: Tag) -> bool:
    if elemento.name != "p":
        return False
        
    clases = [c.lower() for c in _clases_de_elemento(elemento)]
    
    # Excluimos explícitamente párrafos de adscripción, país o detalles finales para no confundirlos con nombres
    if any("adscripcion" in c or "pais" in c or "acerca-del-autor" in c for c in clases):
        return False
        
    # 1. Búsqueda por clase: Atrapa autor_final_2apellidos, autor2, autor, etc. (variantes de InDesign)
    if any("autor" in c for c in clases):
        return True

    # 2. Búsqueda por contexto: Si InDesign le puso un estilo genérico (ParaOverride, Estilo-de-p-rrafo), 
    # analizamos los elementos hermanos siguientes. Si abajo hay una adscripción, país u ORCID, es el autor.
    if any(c.startswith("estilo-de-p-rrafo") or c.startswith("paraoverride") for c in clases):
        for sib in elemento.find_next_siblings(limit=2):
            if not isinstance(sib, Tag):
                continue
            clases_sib = [c.lower() for c in _clases_de_elemento(sib)]
            if any("adscripcion" in c or "pais" in c for c in clases_sib):
                return True
            if _tiene_orcid_en_bloque(sib):
                return True

    return False


def _extraer_autores_desde_elementos(elementos: List[Tag]) -> List[Autor]:
    autores: List[Autor] = []
    idx = 0

    while idx < len(elementos):
        elem = elementos[idx]
        clases = " ".join(_clases_de_elemento(elem)).lower()

        if "resumenfinal" in clases:
            break

        if not _parece_bloque_autor(elem):
            idx += 1
            continue

        nombre = _limpiar_nombre_autor(elem)
        orcid = _extraer_orcid_desde_elemento(elem)
        autor = Autor(nombre=nombre, orcid=orcid)

        idx += 1
        while idx < len(elementos):
            sib = elementos[idx]
            clases_sib = " ".join(_clases_de_elemento(sib)).lower()

            if "resumenfinal" in clases_sib:
                break
            if _parece_bloque_autor(sib):
                idx -= 1
                break

            if "adscripcion" in clases_sib:
                texto = _limpiar_texto(sib)
                orcid_en_ads = _extraer_orcid_desde_elemento(sib)
                if orcid_en_ads and not autor.orcid:
                    autor.orcid = orcid_en_ads
                elif texto:
                    if autor.adscripcion:
                        autor.adscripcion += " | " + texto
                    else:
                        autor.adscripcion = texto
            elif "pais" in clases_sib:
                autor.pais = _limpiar_texto(sib)

            idx += 1

        autores.append(autor)
        idx += 1

    return autores


def _extraer_autores_desde_documento(soup: BeautifulSoup) -> List[Autor]:
    autores: List[Autor] = []
    container = None
    titulo_h1 = soup.find("h1", class_="tcc-final")
    if titulo_h1 is not None:
        container = titulo_h1.find_parent("div")
    if container is None:
        container = soup.find("div", class_="_idGenObjectStyleOverride-2")
    if container is None:
        container = soup.find("div", class_="_idGenObjectStyleOverride-1")
    if container is None:
        container = soup.body
    if container is None:
        return autores

    elementos = [e for e in container.children if isinstance(e, Tag)]
    return _extraer_autores_desde_elementos(elementos)


def extraer_contenido(html_path: str) -> ContenidoArticulo:
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    for span in soup.find_all("span", class_="no-separar"):
        span.unwrap()

    contenido = ContenidoArticulo()

    container = None
    titulo_h1 = soup.find("h1", class_="tcc-final")
    if titulo_h1 is not None:
        container = titulo_h1.find_parent("div")

    if container is None:
        container = soup.find("div", class_="_idGenObjectStyleOverride-2")

    if container is None:
        container = soup.find("div", class_="_idGenObjectStyleOverride-1")

    if container is None:
        container = soup.body
    if container is None:
        return contenido

    elementos = [e for e in container.children if isinstance(e, Tag)]

    contenido.tipo_articulo = _extraer_tipo_desde_marco(soup)
    contenido.tipo_articulo = _normalizar_tipo_articulo(contenido.tipo_articulo)

    idx = 0
    fase = "identificadores"
    autor_actual: Optional[Autor] = None
    textos_identificadores_vistos = set()

    while idx < len(elementos):
        elem = elementos[idx]
        clases = " ".join(_clases_de_elemento(elem))

        if elem.name == "table":
            str_elem = f'<div class="table-responsive">\n{elem}\n</div>'
        else:
            str_elem = str(elem)

        if fase == "identificadores" and ("identificador" in clases):
            html_interno = _obtener_html_interno(elem)
            texto_plano = elem.get_text()
            
            idx_doi = texto_plano.upper().find("DOI:")
            
            if idx_doi != -1:
                prefijo = texto_plano[:idx_doi + 4].strip()
                
                enlace = elem.find("a")
                url_doi = None
                
                if enlace and enlace.has_attr("href") and ("doi.org" in enlace["href"] or "10." in enlace["href"]):
                    url_doi = enlace["href"].strip()
                else:
                    sufijo = texto_plano[idx_doi + 4:]
                    sufijo_limpio = sufijo.replace(" ", "")
                    match = re.search(r'(https?://(?:dx\.)?doi\.org/[^\s]+|10\.\d{4,9}/[-._;()/:A-Z0-9]+)', sufijo_limpio, re.IGNORECASE)
                    if match:
                        url_doi = match.group(1).rstrip(".,;")
                        if not url_doi.startswith("http"):
                            url_doi = "https://doi.org/" + url_doi
                
                if url_doi:
                    html_interno = f'{prefijo} <a href="{url_doi}"><span class="hipervinculo">{url_doi}</span></a>'
            
            texto_comparacion = texto_plano.replace(" ", "").lower()
            
            if texto_comparacion and texto_comparacion not in textos_identificadores_vistos:
                contenido.identificadores.append(html_interno)
                textos_identificadores_vistos.add(texto_comparacion)
                
            idx += 1
            continue

        if elem.name == "h1" and "tcc-final" in clases:
            contenido.titulo_es = _obtener_html_interno(elem)
            fase = "titulo_en"
            idx += 1
            continue

        if fase == "titulo_en" and elem.name == "h2" and "tcc-ingles" in clases:
            contenido.titulo_en = _obtener_html_interno(elem)
            fase = "autores"
            idx += 1
            continue

        if _parece_bloque_autor(elem):
            if autor_actual is not None:
                contenido.autores.append(autor_actual)
            nombre_autor = _limpiar_nombre_autor(elem)
            orcid_autor = _extraer_orcid_desde_elemento(elem)
            autor_actual = Autor(nombre=nombre_autor, orcid=orcid_autor)
            fase = "autor_detalles"
            idx += 1
            continue

        if fase == "autor_detalles":
            if "adscripcion" in clases:
                texto = _limpiar_texto(elem)
                enlace_orcid = _extraer_orcid_desde_elemento(elem)
                if enlace_orcid:
                    if autor_actual and not autor_actual.orcid:
                        autor_actual.orcid = enlace_orcid
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
                fase = "resumen"

        if "resumenfinal" in clases:
            contenido.resumen = _obtener_html_interno(elem)
            fase = "palabras_clave"
            idx += 1
            continue

        if "palabrasclave" in clases:
            contenido.palabras_clave = _obtener_html_interno(elem)
            fase = "abstract"
            idx += 1
            continue

        if "abstract_final" in clases:
            contenido.abstract = _obtener_html_interno(elem)
            fase = "keywords"
            idx += 1
            continue

        if "keywords_final" in clases:
            contenido.keywords = _obtener_html_interno(elem)
            fase = "cuerpo"
            idx += 1
            continue

        if fase == "cuerpo":
            if elem.name == "h3" and "VV" in clases:
                texto_h3 = _limpiar_texto(elem).lower()
                if "referencia" in texto_h3:
                    fase = "referencias"
                    contenido.secciones_cuerpo.append(str_elem)
                    idx += 1
                    continue
                    
            texto_limpio = _limpiar_texto(elem)
            if "recepcion" in clases or texto_limpio.startswith("Recepción:"):
                fase = "postcontenido"
            else:
                texto_upper = texto_limpio.upper()
                if any(texto_upper.startswith(palabra) for palabra in ["TABLA", "GRÁFICA", "GRAFICA", "FIGURA", "IMAGEN", "FUENTE", "NOTA"]):
                    if isinstance(elem, Tag):
                        clases_elem = elem.get("class", [])
                        if isinstance(clases_elem, str):
                            clases_elem = [clases_elem]
                        if "titulo-tabla-imagen" not in clases_elem:
                            clases_elem.append("titulo-tabla-imagen")
                            elem["class"] = clases_elem
                            str_elem = str(elem)

                contenido.secciones_cuerpo.append(str_elem)
                idx += 1
                continue

        if fase == "referencias":
            texto_limpio = _limpiar_texto(elem)
            if "bib" in clases:
                contenido.referencias.append(str_elem)
                idx += 1
                continue
            elif "recepcion" in clases or texto_limpio.startswith("Recepción:"):
                fase = "postcontenido"
            else:
                contenido.referencias.append(str_elem)
                idx += 1
                continue

        if fase == "postcontenido":
            texto_limpio = _limpiar_texto(elem)
            if "como_citar" in clases or texto_limpio.upper() == "CÓMO CITAR":
                fase = "como_citar"
                contenido.como_citar.append(str_elem)
                idx += 1
                continue
                
            if "recepcion" in clases or texto_limpio.startswith("Recepción:"):
                contenido.fechas.append(_obtener_html_interno(elem))
            elif "publicacion" in clases or texto_limpio.startswith("Publicación:"):
                contenido.fechas.append(_obtener_html_interno(elem))
            elif texto_limpio.startswith("Aceptación:") or texto_limpio.startswith("Aceptado:"):
                contenido.fechas.append(_obtener_html_interno(elem))
            elif "acerca-del-autor" in clases or "Estilo-de-p-rrafo-6" in clases:
                contenido.acerca_autores.append(str_elem)
            elif "iijunam" in clases or "APA" in clases:
                fase = "como_citar"
                contenido.como_citar.append(str_elem)
            else:
                pass
            idx += 1
            continue

        if fase == "como_citar":
            if elem.name == "hr" and "HorizontalRule-1" in clases:
                break
            if elem.name == "section" and "_idFootnotes" in clases:
                break
            contenido.como_citar.append(str_elem)
            idx += 1
            continue

        idx += 1

    if autor_actual is not None:
        contenido.autores.append(autor_actual)

    autores_en_doc = _extraer_autores_desde_documento(soup)
    if len(autores_en_doc) > len(contenido.autores):
        contenido.autores = autores_en_doc

    contenido.como_citar = _deduplicar_bloques_html(contenido.como_citar)
    contenido.acerca_autores = _deduplicar_bloques_html(contenido.acerca_autores)

    seccion_notas = soup.find("section", class_="_idFootnotes")
    if seccion_notas:
        contenido.notas_html = str(seccion_notas)

    return contenido

def _corregir_rutas_imagenes(html: str) -> str:
    def reemplazar_y_sanitizar(match):
        nombre_original = match.group(1)
        nombre = urllib.parse.unquote(nombre_original)
        nombre = unicodedata.normalize('NFKD', nombre).encode('ASCII', 'ignore').decode('utf-8')
        nombre = re.sub(r'[^\w\.-]', '_', nombre)
        
        return f'src="images/{nombre}"'

    html = re.sub(
        r'src="[^"]*?(?:web-resources/image/|image/)([^"]+)"',
        reemplazar_y_sanitizar,
        html,
    )
    return html

def _corregir_rutas_footnotes(html: str) -> str:
    html = re.sub(
        r'href="[^"#]*\.html(#[^"]+)"',
        r'href="\1"',
        html,
    )
    return html

def _generar_bloque_autor(autor: Autor) -> str:
    lineas = []
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
    if autor.adscripcion:
        lineas.append(f'<p class="adscripcion">{autor.adscripcion}</p>')
    if autor.pais:
        lineas.append(f'<p class="pais">{autor.pais}</p>')
    return "\n\t\t\t".join(lineas)

def generar_html_referencia(
    contenido: ContenidoArticulo,
    archivos_css: List[str],
    nombre_revista: str,
) -> str:
    css_links = []
    for css_file in archivos_css:
        css_links.append(f'\t\t<link href="css/{css_file}" rel="stylesheet" type="text/css" />')
    css_links_str = "\n".join(css_links)

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

    tipo_articulo = contenido.tipo_articulo or "Artículo"
    tipo_clase = ""
    if _clave_tipo_articulo(tipo_articulo) != "articulo":
        tipo_clase = " tipo-no-articulo"
        
    marco_html = f"""
\t\t\t<div id="_idContainer000" class="Marco-de-texto-b-sico _idGenObjectStyleOverride-1">
\t\t\t\t<p class="body_text2{tipo_clase}"><span>{tipo_articulo}</span></p>
\t\t\t</div>"""

    autores_html = "\n\t\t\t".join(_generar_bloque_autor(a) for a in contenido.autores)
    resumen_html = f'<p class="resumenfinal ParaOverride-5">{contenido.resumen}</p>' if contenido.resumen else ""
    palabras_html = f'<p class="palabrasclave">{contenido.palabras_clave}</p>' if contenido.palabras_clave else ""
    abstract_html = f'<p class="abstract_final" lang="en-US">{contenido.abstract}</p>' if contenido.abstract else ""
    keywords_html = f'<p class="keywords_final">{contenido.keywords}</p>' if contenido.keywords else ""
    cuerpo_html = "\n\t\t\t".join(contenido.secciones_cuerpo)
    referencias_html = "\n\t\t\t".join(contenido.referencias)

    bloques_post = []

    if contenido.fechas:
        bloques_post.append('<hr class="HorizontalRule-1" />')
        for i, fecha in enumerate(contenido.fechas):
            if i == 0:
                bloques_post.append(f'<p class="recepcion">{fecha}</p>')
            elif "Aceptación" in fecha or "Aceptado" in fecha:
                bloques_post.append(f'<p class="acerca-del-autor">{fecha}</p>')
            else:
                bloques_post.append(f'<p class="publicacion">{fecha}</p>')
        bloques_post.append('<hr class="HorizontalRule-1" />')

    if contenido.acerca_autores:
        bloques_post.extend(contenido.acerca_autores)
        
    if contenido.como_citar:
        if bloques_post and bloques_post[-1] != '<hr class="HorizontalRule-1" />':
            bloques_post.append('<hr class="HorizontalRule-1" />')
        elif not bloques_post:
            bloques_post.append('<hr class="HorizontalRule-1" />')
        citas_unidas = "\n\t\t\t\t".join(contenido.como_citar)
        bloques_post.append(f'<div class="como_citar_section">\n\t\t\t\t{citas_unidas}\n\t\t\t</div>')

    if contenido.notas_html:
        if bloques_post and bloques_post[-1] != '<hr class="HorizontalRule-1" />':
            bloques_post.append('<hr class="HorizontalRule-1" />')
        elif not bloques_post:
            bloques_post.append('<hr class="HorizontalRule-1" />')
        bloques_post.append(contenido.notas_html)

    post_html = "\n\t\t\t".join(bloques_post)

    html = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="es-ES">
\t<head>
\t\t<meta charset="utf-8" />
\t\t<meta name="viewport" content="width=device-width, initial-scale=1.0" />
\t\t<title>{nombre_revista}</title>
{css_links_str}
\t</head>
\t<body id="x{nombre_revista}">
\t\t<div class="contenedor">
{marco_html}
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
\t\t\t{post_html}
\t\t</div>
\t</div>
\t</body>
</html>"""

    html = _corregir_rutas_imagenes(html)
    html = _corregir_rutas_footnotes(html)
    return html

def procesar_html(
    html_path: str,
    archivos_css: List[str],
    ruta_salida_html: str,
    nombre_revista: str,
    tipo_articulo_forzado: Optional[str] = None,
) -> bool:
    try:
        contenido = extraer_contenido(html_path)
        if tipo_articulo_forzado:
            normalizado = contenido.tipo_articulo.lower().replace(" ", "")
            forzado = tipo_articulo_forzado.lower().replace(" ", "")
            if not contenido.tipo_articulo or normalizado == forzado:
                contenido.tipo_articulo = tipo_articulo_forzado
        html_final = generar_html_referencia(contenido, archivos_css, nombre_revista)

        with open(ruta_salida_html, "w", encoding="utf-8") as f:
            f.write(html_final)
        return True

    except Exception as e:
        print(f"    ✗ Error procesando HTML: {e}")
        import traceback
        traceback.print_exc()
        return False

def _limpiar_texto_simple(html_str: str) -> str:
    soup = BeautifulSoup(html_str, "html.parser")
    return soup.get_text(strip=True)