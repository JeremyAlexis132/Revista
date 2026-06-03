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
    otros_postcontenido: List[str] = field(default_factory=list)
    notas_html: str = ""
    cuerpo_html_crudo: str = ""

ORCID_SVG = """<span class="_idSVGInline"><svg version="1.1" xmlns="https://lh7-rt.googleusercontent.com/docsz/AD_4nXfwdGXelHGv7MlGZDMGvyU2eVt42E2zw-ycbLEvUNupHXL3Z0aYtEc3I-N4UdW7pgx6-40X_NoZRG15-rwBd_nnmxPJNxRjl4cV47oLrQ4qPWekGK08Pu6hdms7SHxNAZ0S7Bzq4OP7a85Vr0kz6NuIytSy?key=FVu4pMW4OSNP023W3l6MTA" x="0px" y="0px" viewBox="0 0 256 256" xml:space="preserve">
<style type="text/css">.st0{fill:#A6CE39;}.st1{fill:#FFFFFF;}</style>
<circle class="st0" cx="128" cy="128" r="128"/>
<g>
<path class="st1" d="M86.3,186.2H70.9V79.1h15.4v48.4V186.2z"/>
<path class="st1" d="M108.9,79.1h41.6c39.6,0,57,28.3,57,53.6c0,27.5-21.5,53.6-56.8,53.6h-41.8V79.1z M124.3,172.4h24.5
c34.9,0,42.9-26.5,42.9-39.7c0-21.5-13.7-39.7-43.7-39.7h-23.7V172.4z"/>
<path class="st1" d="M88.7,56.8c0,5.5-4.5,10.1-10.1,10.1c-5.6,0-10.1-4.6-10.1-10.1c0-5.6,4.5-10.1,10.1-10.1
C84.2,46.7,88.7,51.3,88.7,56.8z"/>
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

def _es_otros_postcontenido(texto: str) -> bool:
    if not texto:
        return False
    texto_upper = texto.upper()
    kws = (
        "FUNDING STATEMENT", "CONFLICTS OF INTEREST", "CONFLICTO DE INTERÉS", 
        "CONFLICTO DE INTERES", "FINANCIAMIENTO", "AGRADECIMIENTO", 
        "DECLARACIÓN", "DECLARACION", "DATA AVAILABILITY", "FUNDING",
        "ANEXO", "ANEXOS", "APPENDIX", "APPENDICES", "APÉNDICE", "APÉNDICES",
        "APENDICE", "APENDICES"
    )
    return any(texto_upper.startswith(kw) for kw in kws)

def _es_acerca_de_autor(texto: str, clases: str) -> bool:
    clases_lower = clases.lower()
    if "acerca-del-autor" in clases_lower or "estilo-de-p-rrafo-6" in clases_lower:
        return True
    texto_lower = texto.lower()
    if "correo electrónico:" in texto_lower or "email:" in texto_lower:
        return True
    return False

def _es_fecha(texto: str, clases: str) -> bool:
    t_lower = texto.lower().strip()
    c_lower = clases.lower()
    if any(x in c_lower for x in ["recepcion", "publicacion", "aceptacion", "recibido", "aceptado", "aprobacion", "publicado"]):
        return True
    if any(t_lower.startswith(x) for x in ["recepción:", "recibido:", "aceptación:", "aceptado:", "aprobación:", "aprobado:", "publicación:", "publicado:"]):
        return True
    return False

def _extraer_url_doi(texto: str) -> str:
    if not texto:
        return ""
    texto_limpio = texto.replace(" ", "")
    match = re.search(
        r"(https?://(?:dx\.)?doi\.org/[^\s]+|10\.\d{4,9}/[-._;()/:A-Z0-9]+)",
        texto_limpio,
        re.IGNORECASE,
    )
    if not match:
        return ""
    url = match.group(1).rstrip(".,;")
    if not url.startswith("http"):
        url = "https://doi.org/" + url
    return url

def _normalizar_identificador_html(elemento: Tag, texto_plano: str) -> str:
    clases = " ".join(_clases_de_elemento(elemento)).lower()
    if "identificadorfinal" in clases:
        return texto_plano
    if "creative commons" in (texto_plano or "").lower():
        cc_url = "https://creativecommons.org/licenses/by/4.0/"
        match = re.search(r"^(.*?)(Licencia\s+Creative\s+Commons[^.]*)(\.?$)", texto_plano.strip(), re.IGNORECASE)
        if match:
            prefijo = match.group(1).strip()
            licencia = match.group(2).strip()
            if prefijo:
                return f'{prefijo} <a href="{cc_url}"><span class="hipervinculo">{licencia}</span></a>'
            return f'<a href="{cc_url}"><span class="hipervinculo">{licencia}</span></a>'
    if "doi" in (texto_plano or "").lower():
        url_doi = ""
        url_doi_texto = _extraer_url_doi(texto_plano)
        enlace = elemento.find("a", href=True)
        if enlace and enlace.get("href"):
            href = enlace["href"].strip()
            if "doi.org" in href or "10." in href:
                url_doi = href
        if url_doi_texto and (not url_doi or url_doi.lower() != url_doi_texto.lower()):
            url_doi = url_doi_texto
        elif not url_doi:
            url_doi = url_doi_texto
        if url_doi:
            prefijo = texto_plano
            match = re.search(r"\bDOI\s*:\s*", texto_plano, re.IGNORECASE)
            if match:
                prefijo = texto_plano[:match.end()].strip()
            else:
                prefijo = texto_plano.replace(url_doi, "").strip()
                if prefijo.endswith(":"):
                    prefijo = prefijo.rstrip()
            if prefijo:
                return f'{prefijo} <a href="{url_doi}"><span class="hipervinculo">{url_doi}</span></a>'
            return f'<a href="{url_doi}"><span class="hipervinculo">{url_doi}</span></a>'
    return _obtener_html_interno(elemento)

def _generar_identificadores_faltantes(contenido: ContenidoArticulo, nombre_revista: str) -> List[str]:
    """Genera el bloque de metadatos inicial si este fue omitido en la exportación de InDesign."""
    if contenido.identificadores:
        return contenido.identificadores

    revista_id = str(nombre_revista.split('_')[0])
    
    vol_num = "[Vol(Núm)]"
    meses_ano = "[Meses de Año]"
    e_id = f"e{revista_id}"
    doi_html = '<span class="hipervinculo">[colocar doi aquí]</span>'

    for cita in contenido.como_citar:
        texto_plano = BeautifulSoup(cita, "html.parser").get_text()
        if "Revista Mexicana de Derecho Electoral" in texto_plano:
            match_vol = re.search(r'vol\.\s*(\d+),\s*núm\.\s*(\d+),\s*([^,]+),\s*(e\d+)', texto_plano, re.IGNORECASE)
            if match_vol:
                vol_num = f"{match_vol.group(1)}({match_vol.group(2)})"
                meses_ano = match_vol.group(3).strip()
                e_id = match_vol.group(4).strip()
            
            # Buscar todos los DOIs posibles en el texto
            matches_doi = re.findall(r'(https?://(?:dx\.)?doi\.org/[^\s]+)', texto_plano, re.IGNORECASE)
            for doi_match in matches_doi:
                doi_url = doi_match.rstrip(".,;")
                # Validación estricta: el DOI debe terminar con el ID de la revista
                if doi_url.endswith(revista_id):
                    doi_html = f'<a href="{doi_url}"><span class="hipervinculo">{doi_url}</span></a>'
                    break
            break

    line1 = f"Revista Mexicana de Derecho Electoral, {vol_num}, {meses_ano}, {e_id}"
    line2 = f'e-ISSN: 2448-7910  DOI: {doi_html}'
    line3 = 'Esta obra está bajo una <a href="https://creativecommons.org/licenses/by/4.0/"><span class="hipervinculo">Licencia Creative Commons Reconocimiento 4.0 Internacional</span></a>'
    line4 = '<span class="hipervinculo">Instituto de Investigaciones Jurídicas de la Universidad Nacional Autónoma de México</span>'

    return [line1, line2, line3, line4]

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

def _parece_bloque_autor(elemento: Tag) -> bool:
    if elemento.name != "p":
        return False
    clases = [c.lower() for c in _clases_de_elemento(elemento)]
    if any("adscripcion" in c or "pais" in c or "acerca-del-autor" in c for c in clases):
        return False
    if any("autor" in c for c in clases):
        return True
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
                        separador = " | " if "|" in autor.adscripcion or "|" in texto else "\n"
                        autor.adscripcion += separador + texto
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
        texto_limpio = _limpiar_texto(elem)
        
        if fase in ["identificadores", "titulo_en", "autores", "autor_detalles", "resumen", "palabras_clave", "abstract", "keywords"]:
            if elem.name in ["h1", "h2", "h3"] or "VV" in clases:
                if not ("tcc-final" in clases or "tcc-ingles" in clases):
                    fase = "cuerpo"
        
        if elem.name == "table":
            str_elem = f'<div class="table-responsive">\n{elem}\n</div>'
        else:
            str_elem = str(elem)

        if fase == "identificadores" and ("identificador" in clases):
            texto_plano = elem.get_text(" ", strip=True)
            html_interno = _normalizar_identificador_html(elem, texto_plano)
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
                            separador = " | " if "|" in autor_actual.adscripcion or "|" in texto else "\n"
                            autor_actual.adscripcion += separador + texto
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

        if fase == "keywords":
            if "keywords_final" in clases or "palabrasclave" in clases or texto_limpio.upper().startswith("KEYWORDS"):
                contenido.keywords = _obtener_html_interno(elem)
                fase = "cuerpo"
                idx += 1
                continue

        if fase == "cuerpo":
            if elem.name == "h3" and "VV" in clases:
                texto_h3 = texto_limpio.lower()
                if "referencia" in texto_h3:
                    fase = "referencias"
                    contenido.secciones_cuerpo.append(str_elem)
                    idx += 1
                    continue
            
            if _es_fecha(texto_limpio, clases) or _es_otros_postcontenido(texto_limpio) or _es_acerca_de_autor(texto_limpio, clases):
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
            es_otros = _es_otros_postcontenido(texto_limpio)
            es_acerca_de_autor = _es_acerca_de_autor(texto_limpio, clases)
            es_fecha = _es_fecha(texto_limpio, clases)
            
            if "bib" in clases and not es_otros and not es_acerca_de_autor and not es_fecha:
                contenido.referencias.append(str_elem)
                idx += 1
                continue
            elif es_fecha or es_otros or es_acerca_de_autor or elem.name == "hr":
                fase = "postcontenido"
            else:
                contenido.referencias.append(str_elem)
                idx += 1
                continue

        if fase == "postcontenido":
            if "como_citar" in clases or texto_limpio.upper() == "CÓMO CITAR":
                fase = "como_citar"
                contenido.como_citar.append(str_elem)
                idx += 1
                continue
            
            if _es_fecha(texto_limpio, clases):
                contenido.fechas.append(_obtener_html_interno(elem).strip())
            elif _es_acerca_de_autor(texto_limpio, clases):
                if isinstance(elem, Tag):
                    clases_elem = elem.get("class", [])
                    if isinstance(clases_elem, str):
                        clases_elem = [clases_elem]
                    clases_limpias = [c for c in clases_elem if c.lower() not in ["body_text", "paraoverride-1", "paraoverride-2"]]
                    if "acerca-del-autor" not in clases_limpias:
                        clases_limpias.append("acerca-del-autor")
                    elem["class"] = clases_limpias
                    str_elem = str(elem)
                contenido.acerca_autores.append(str_elem)
            elif "iijunam" in clases or "APA" in clases:
                fase = "como_citar"
                contenido.como_citar.append(str_elem)
            else:
                if elem.name not in ["hr", "section"]:
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
                    contenido.otros_postcontenido.append(str_elem)
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
        return f'src="{nombre}"'

    html = re.sub(
        r'src="[^"]*?(?:web-resources/image/|image/)([^"]+)"',
        reemplazar_y_sanitizar,
        html,
    )
    return html

def _corregir_rutas_footnotes(html: str) -> str:
    html = re.sub(r'href="[^"#]*\.html(#[^"]+)"', r'href="\1"', html)
    return html

def _generar_bloque_autor(autor: Autor) -> str:
    lineas = []
    orcid_html = ""
    if autor.orcid:
        orcid_html = (f' <span class="Versalitas"><a href="{autor.orcid}">{ORCID_SVG}</a></span>')
    lineas.append(f'<p class="autor_final_2apellidos ORCID2">{autor.nombre}{orcid_html}</p>')
    if autor.adscripcion:
        if "\n" in autor.adscripcion:
            for linea in (parte.strip() for parte in autor.adscripcion.split("\n")):
                if linea:
                    lineas.append(f'<p class="adscripcion">{linea}</p>')
        else:
            lineas.append(f'<p class="adscripcion">{autor.adscripcion}</p>')
    if autor.pais:
        lineas.append(f'<p class="pais">{autor.pais}</p>')
    return "\n\t\t\t".join(lineas)

def generar_html_referencia(
    contenido: ContenidoArticulo,
    css_inline: str,
    nombre_revista: str,
) -> str:
    
    css_tags = f"<style>\n{css_inline}\n\t\t</style>"

    identificadores_lista = contenido.identificadores
    if not identificadores_lista:
        identificadores_lista = _generar_identificadores_faltantes(contenido, nombre_revista)

    identificadores_html = ""
    separador_identificadores = ""
    
    if identificadores_lista:
        id_lines = []
        for i, ident in enumerate(identificadores_lista):
            if i < len(identificadores_lista) - 1:
                id_lines.append(f'<br>{ident}')
            else:
                id_lines.append(f'<br>{ident}<br><br>')
        identificadores_html = f"""\n\t\t<p class="notas_iniciales">\t\n\t\t\t{''.join(id_lines)}\n\t\t</p>"""
        separador_identificadores = '\n\t\t<hr class="HorizontalRule-1" />'

    tipo_articulo = contenido.tipo_articulo or "Artículo"
    tipo_clase = ""
    if _clave_tipo_articulo(tipo_articulo) != "articulo":
        tipo_clase = " tipo-no-articulo"
        
    marco_html = f"""\n\t\t\t<div id="_idContainer000" class="Marco-de-texto-b-sico _idGenObjectStyleOverride-1">\n\t\t\t\t<p class="body_text2{tipo_clase}"><span>{tipo_articulo}</span></p>\n\t\t\t</div>"""

    autores_html = "\n\t\t\t".join(_generar_bloque_autor(a) for a in contenido.autores)
    resumen_html = f'<p class="resumenfinal ParaOverride-5">{contenido.resumen}</p>' if contenido.resumen else ""
    palabras_html = f'<p class="palabrasclave">{contenido.palabras_clave}</p>' if contenido.palabras_clave else ""
    abstract_html = f'<p class="abstract_final" lang="en-US">{contenido.abstract}</p>' if contenido.abstract else ""
    keywords_html = f'<p class="keywords_final">{contenido.keywords}</p>' if contenido.keywords else ""
    cuerpo_html = "\n\t\t\t".join(contenido.secciones_cuerpo)
    referencias_html = "\n\t\t\t".join(contenido.referencias)

    bloques_post = []

    if contenido.otros_postcontenido:
        otros_validos = []
        for html_chunk in contenido.otros_postcontenido:
            soup_chunk = BeautifulSoup(html_chunk, "html.parser")
            texto_plano = soup_chunk.get_text().replace('\xa0', '').replace('\u200b', '').strip()
            if texto_plano or soup_chunk.find(["img", "svg", "table"]):
                otros_validos.append(html_chunk)
        if otros_validos:
            bloques_post.extend(otros_validos)

    if contenido.fechas:
        fechas_validas = []
        for fecha in contenido.fechas:
            if fecha.strip():
                fechas_validas.append(fecha.strip())
        
        if fechas_validas:
            def sort_fechas(f):
                f_low = f.lower()
                if "recep" in f_low or "recibi" in f_low: return 1
                if "acept" in f_low or "aprob" in f_low: return 2
                if "publi" in f_low: return 3
                return 4
                
            fechas_validas.sort(key=sort_fechas)

            if not bloques_post or bloques_post[-1] != '<hr class="HorizontalRule-1" />':
                bloques_post.append('<hr class="HorizontalRule-1" />')
            
            fechas_unidas = "<br>\n\t\t\t\t".join(fechas_validas)
            bloques_post.append(f'<p class="recepcion">{fechas_unidas}</p>')
            bloques_post.append('<hr class="HorizontalRule-1" />')

    if contenido.acerca_autores:
        autores_validos = []
        for autor_html in contenido.acerca_autores:
            texto_plano = BeautifulSoup(autor_html, "html.parser").get_text().replace('\xa0', '').replace('\u200b', '').strip()
            if texto_plano:
                autores_validos.append(autor_html)
        if autores_validos:
            if not bloques_post or bloques_post[-1] != '<hr class="HorizontalRule-1" />':
                bloques_post.append('<hr class="HorizontalRule-1" />')
            bloques_post.extend(autores_validos)
        
    if contenido.como_citar:
        citas_validas = []
        for cita_html in contenido.como_citar:
            texto_plano = BeautifulSoup(cita_html, "html.parser").get_text().replace('\xa0', '').replace('\u200b', '').strip()
            if texto_plano:
                citas_validas.append(cita_html)
        if citas_validas:
            if not bloques_post or bloques_post[-1] != '<hr class="HorizontalRule-1" />':
                bloques_post.append('<hr class="HorizontalRule-1" />')
            citas_unidas = "\n\t\t\t\t".join(citas_validas)
            bloques_post.append(f'<div class="como_citar_section">\n\t\t\t\t{citas_unidas}\n\t\t\t</div>')

    if contenido.notas_html:
        if not bloques_post or bloques_post[-1] != '<hr class="HorizontalRule-1" />':
            bloques_post.append('<hr class="HorizontalRule-1" />')
        bloques_post.append(contenido.notas_html)

    post_html = "\n\t\t\t".join(bloques_post)
    separador_referencias = ""
    if post_html and (referencias_html or cuerpo_html):
        if not post_html.lstrip().startswith("<hr"):
            separador_referencias = "\n\t\t\t<hr class=\"HorizontalRule-1\" />"

    html = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="es-ES">
\t<head>
\t\t<meta charset="utf-8" />
\t\t<meta name="viewport" content="width=device-width, initial-scale=1.0" />
\t\t<title>{nombre_revista}</title>
\t\t{css_tags}
\t</head>
\t<body id="x{nombre_revista}">
\t\t<div class="contenedor">
{marco_html}
{identificadores_html}{separador_identificadores}
\t\t<div id="_idContainer003" class="_idGenObjectStyleOverride-2">
\t\t\t<h1 class="tcc-final">{contenido.titulo_es}</h1>
\t\t\t<h2 class="tcc-ingles" lang="en-US">{contenido.titulo_en}</h2>
\t\t\t{autores_html}
\t\t\t{resumen_html}
\t\t\t{palabras_html}
\t\t\t{abstract_html}
\t\t\t{keywords_html}
\t\t\t{cuerpo_html}
\t\t\t{referencias_html}{separador_referencias}
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
    css_inline: str,
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
        html_final = generar_html_referencia(contenido, css_inline, nombre_revista)

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