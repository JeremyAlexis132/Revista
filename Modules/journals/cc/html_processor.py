"""
Módulo para extraer y reestructurar HTML específico de CC.
Arma el documento siguiendo el formato visual de RMDE, solucionando bugs de CC,
errores tipográficos en DOI, fechas fragmentadas y neutralizando saltos de línea forzados.
"""

import re
import urllib.parse
import unicodedata
from typing import List, Optional
from dataclasses import dataclass, field
from bs4 import BeautifulSoup, Tag

# ----------------------------------------------------------------------
# NORMALIZACIÓN DE ESTILOS DE INDESIGN
# Algunos artículos (p. ej. 19395) se exportan con estilos de párrafo
# prefijados ("ESTILOS-FINALES_TCC-1", "ESTILOS-FINALES_VV", ...) y con
# <p> en lugar de <h1>/<h2>/<h3>. Otros (p. ej. 20819) ya vienen con los
# nombres limpios. Aquí se lleva todo al esquema limpio que entiende el CSS.
# ----------------------------------------------------------------------
_RE_PREFIJO_ESTILO = re.compile(r"^ESTILOS[-_]FINALES[-_]", re.IGNORECASE)

# clase (minúsculas, ya sin prefijo) -> (etiqueta, clase semántica)
_MAPA_ESTILOS_SEMANTICOS = {
    "tcc-1": ("h1", "titulo_espanol"),
    "tcc-2": ("h2", "titulo_ingles"),
    "vv":    ("h3", "romanos"),
    "ia":    ("h4", "arabigos"),
    "is":    ("h5", "subarabigos"),
}

_KW_COMO_CITAR = ["cómo citar", "como citar", "how to cite", "comment citer"]
_RE_KEYWORDS_EN = re.compile(r"^\s*(keywords?|key\s+words|mots[\s-]*cl[eé]s?)\b", re.IGNORECASE)

def _normalizar_clases_indesign(soup: BeautifulSoup) -> None:
    """Quita el prefijo ESTILOS-FINALES_ y convierte los <p> de título y
    encabezados a etiquetas semánticas (h1..h5) con las clases que usa el CSS."""
    for tag in soup.find_all(True):
        clases = tag.get("class")
        if not clases:
            continue
        nuevas = [_RE_PREFIJO_ESTILO.sub("", c) for c in clases]

        if tag.name in ("p", "div"):
            for i, c in enumerate(nuevas):
                destino = _MAPA_ESTILOS_SEMANTICOS.get(c.lower())
                if destino:
                    tag.name = destino[0]
                    nuevas[i] = destino[1]
                    break
        tag["class"] = nuevas

def _reetiquetar_parrafo(elem: Tag, clase: str, texto: str) -> None:
    """Deja el elemento como <p class="..."> con texto plano (sin spans de InDesign)."""
    elem.name = "p"
    elem["class"] = [clase]
    elem.clear()
    elem.append(texto)

def _es_titulo_declaracion(elem: Tag, texto_lower: str, palabras: List[str]) -> bool:
    """Un encabezado de declaración ética debe *ser* la palabra clave (con o sin
    numeración/puntuación), no simplemente contenerla dentro de un título largo."""
    base = re.sub(r"^\s*(?:[ivxlc]+|\d+)[.)]\s+", "", texto_lower.strip())
    base = base.strip(" .:;–—-")
    if base in palabras:
        return True
    es_encabezado = elem.name.startswith("h") or "romanos" in (elem.get("class") or []) or "arabigos" in (elem.get("class") or [])
    return es_encabezado and len(base) < 60 and any(base.startswith(kw) for kw in palabras)

@dataclass
class Autor:
    nombre_html: str = ""
    orcid_url: str = ""
    adscripciones_html: List[str] = field(default_factory=list)

@dataclass
class ContenidoArticulo:
    identificadores: List[str] = field(default_factory=list)
    tipo_articulo: str = "Artículo"
    titulo_es: str = ""
    titulo_en: str = ""
    autores_obj: List[Autor] = field(default_factory=list)
    resumen: str = ""
    palabras_clave: str = ""
    abstract: str = ""
    keywords: str = ""
    secciones_cuerpo: List[str] = field(default_factory=list)
    referencias: List[str] = field(default_factory=list)
    declaraciones_etica: List[str] = field(default_factory=list)
    fechas: List[str] = field(default_factory=list)
    como_citar: List[str] = field(default_factory=list)
    notas_html: str = ""
    doi_extraido: str = ""

def _obtener_html_interno(elemento: Tag) -> str:
    return "".join(str(child) for child in elemento.children) if elemento else ""

def _indentar_html(lista_html: List[str], tabs: int) -> str:
    if not lista_html:
        return ""
    espaciado = "\n" + ("\t" * tabs)
    return espaciado.join(item.replace("\n", espaciado) for item in lista_html)

def _extraer_url_doi(texto: str) -> str:
    match = re.search(r"(https?://(?:dx\.)?doi\.org/[^\s<>\"']+)", texto.replace(" ", ""), re.IGNORECASE)
    if not match: 
        match = re.search(r"(10\.\d{4,9}/[-._;()/:A-Z0-9]+)", texto.replace(" ", ""), re.IGNORECASE)
    if not match: return ""
    url = match.group(1).rstrip(".,;<>\"'")
    url = url if url.startswith("http") else "https://doi.org/" + url
    url = url.replace("10.22201/iij/", "10.22201/iij.")
    return url

def _generar_identificadores_cc(contenido: ContenidoArticulo, nombre_revista: str) -> List[str]:
    revista_id = str(nombre_revista.split('_')[0])
    vol_num = "[Vol(Núm)]"
    meses_ano = "[Meses de Año]"
    e_id = f"e{revista_id}"
    doi_html = '<span class="hipervinculo">[colocar doi aquí]</span>'

    for cita in contenido.como_citar:
        texto_plano = BeautifulSoup(cita, "html.parser").get_text()
        if "Cuestiones Constitucionales" in texto_plano:
            vol_match = re.search(r'vol[^\d]*(\d+)', texto_plano, re.IGNORECASE)
            num_match = re.search(r'n[úu]m[^\d]*(\d+)', texto_plano, re.IGNORECASE)
            mes_match = re.search(r'([a-zA-Z]+\s*-\s*[a-zA-Z]+\s+(?:de\s+)?\d{4})', texto_plano, re.IGNORECASE)
            eid_match = re.search(r'(e\d{4,6})', texto_plano, re.IGNORECASE)

            if vol_match and num_match:
                vol_num = f"{vol_match.group(1)}({num_match.group(1)})"
            if mes_match:
                meses_ano = mes_match.group(1).strip()
            if eid_match:
                e_id = eid_match.group(1).strip()
                
            matches_doi = re.findall(r"(https?://(?:dx\.)?doi\.org/[^\s<>\"']+)", texto_plano, re.IGNORECASE)
            if matches_doi:
                doi_url = matches_doi[0].rstrip(".,;<>\"'").replace("10.22201/iij/", "10.22201/iij.")
                doi_html = f'<a href="{doi_url}"><span class="hipervinculo">{doi_url}</span></a>'
            break

    if not '<a' in doi_html and contenido.doi_extraido:
         doi_html = f'<a href="{contenido.doi_extraido}"><span class="hipervinculo">{contenido.doi_extraido}</span></a>'

    line1 = f"Cuestiones Constitucionales. Revista Mexicana de Derecho Constitucional, {vol_num}, {meses_ano}, {e_id}"
    line2 = f'e-ISSN: 2448-4881  DOI: {doi_html}'
    line3 = 'Esta obra está bajo una <a href="https://creativecommons.org/licenses/by-nc/4.0/"><span class="hipervinculo">Licencia Creative Commons Reconocimiento-NoComercial 4.0 Internacional</span></a>'
    line4 = 'Instituto de Investigaciones Jurídicas de la Universidad Nacional Autónoma de México'

    return [line1, line2, line3, line4]

def extraer_contenido(html_path: str) -> ContenidoArticulo:
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
        
    # ==============================================================
    # LIMPIEZA DE SALTOS DE LÍNEA Y CARACTERES INVISIBLES DE INDESIGN
    # ==============================================================
    for br in soup.find_all("br"):
        br.replace_with(" ")

    for text_node in soup.find_all(string=True):
        if '\xad' in text_node or '\u200b' in text_node:
            text_node.replace_with(text_node.replace('\xad', '').replace('\u200b', ''))

    for span in soup.find_all("span", class_="no-separar"):
        span.unwrap()

    _normalizar_clases_indesign(soup)
        
    for img in soup.find_all("img"):
        if "logo_findearticulo" in img.get("src", "").lower() or "logo_cc_fin" in img.get("src", "").lower():
            if img.parent: img.parent.decompose()
            
    contenido = ContenidoArticulo()
    container = soup.find("div", class_="_idGenObjectStyleOverride-1") or soup.body
    if not container: return contenido
        
    elementos = [e for e in container.children if isinstance(e, Tag)]
    fase = "inicio"
    autor_actual: Optional[Autor] = None
    capturando_fecha_fragmentada = False

    for elem in elementos:
        clases = " ".join(elem.get("class", [])).lower()
        texto_limpio = elem.get_text(strip=False).strip()
        texto_lower = texto_limpio.lower()
        str_elem = str(elem)

        if elem.name == "section" and "_idfootnotes" in clases:
            continue

        if "doi" in clases or texto_lower.startswith("doi:"):
            contenido.doi_extraido = _extraer_url_doi(texto_limpio)
            continue

        is_date_class = "recepcion" in clases or "aceptacion-publicacion" in clases or "recibido-y-aceptado-final" in clases
        has_date_kw = bool(re.search(r'\b(recepci[óo]n|recibido|aceptaci[óo]n|aceptado|publicaci[óo]n|publicado|aprobaci[óo]n|aprobado)\b', texto_lower))
        has_digits = bool(re.search(r'\d', texto_lower))
        is_email_or_inst = "@" in texto_lower or "universidad" in texto_lower or "instituto" in texto_lower or "facultad" in texto_lower

        es_fecha = False
        if is_date_class and not is_email_or_inst:
            es_fecha = True
        elif fase == "inicio" and has_date_kw and len(texto_limpio) < 150 and not is_email_or_inst:
            es_fecha = True

        if is_date_class and not es_fecha and autor_actual and fase == "inicio":
            autor_actual.adscripciones_html.append(_obtener_html_interno(elem))
            capturando_fecha_fragmentada = False
            continue

        if es_fecha:
            if contenido.fechas and len(contenido.fechas[-1]) < 30 and not bool(re.search(r'\d', contenido.fechas[-1])):
                contenido.fechas[-1] += " " + texto_limpio
            else:
                contenido.fechas.append(texto_limpio)
            capturando_fecha_fragmentada = not has_digits
            continue
        elif capturando_fecha_fragmentada and has_digits and len(texto_limpio) < 50:
            if contenido.fechas:
                contenido.fechas[-1] += " " + texto_limpio
            capturando_fecha_fragmentada = False
            continue
        else:
            capturando_fecha_fragmentada = False

        if "titulo_espanol" in clases or "tcc-1" in clases:
            contenido.titulo_es = str_elem
            continue
            
        if "titulo_ingles" in clases or "tcc-2" in clases:
            contenido.titulo_en = str_elem
            continue

        if "aut-dos-nombres" in clases or "aut" in clases.split() or "estilos-finales_aut" in clases:
            if autor_actual:
                contenido.autores_obj.append(autor_actual)
            autor_actual = Autor(nombre_html=_obtener_html_interno(elem))
            continue
            
        if "orcid" in clases:
            if autor_actual:
                enlace = elem.find("a", href=True)
                if enlace and enlace.get("href"):
                    autor_actual.orcid_url = enlace["href"].strip()
                else:
                    match = re.search(r"(https?://orcid\.org/[^\s]+)", texto_limpio)
                    if match: autor_actual.orcid_url = match.group(1).strip()
            continue

        if fase == "inicio" and autor_actual and ("nota-de-autor-final" in clases or "adscripcion" in clases or "correo" in clases or "@" in texto_limpio or "universidad" in texto_lower or "instituto" in texto_lower or "facultad" in texto_lower):
            if len(texto_limpio) < 200: 
                autor_actual.adscripciones_html.append(_obtener_html_interno(elem))
                continue

        if "resumen" in clases and "resumen_ingles" not in clases:
            contenido.resumen = str_elem
            fase = "cuerpo"
            continue
            
        if "palabras-clave" in clases:
            # En algunos artículos "Keywords" también viene con la clase palabras-clave
            if _RE_KEYWORDS_EN.match(texto_limpio) or (contenido.palabras_clave and not contenido.keywords):
                elem["class"] = ["keywords"]
                contenido.keywords = str(elem)
            else:
                contenido.palabras_clave = str_elem
            continue

        if "resumen_ingles" in clases:
            contenido.abstract = str_elem
            continue

        if "keywords" in clases:
            contenido.keywords = str_elem
            continue

        if texto_lower in _KW_COMO_CITAR:
            _reetiquetar_parrafo(elem, "como_citar", texto_limpio)
            contenido.como_citar.append(str(elem))
            fase = "como_citar"
            continue
        if fase == "como_citar" and texto_lower in ("iij-unam", "iijunam", "iij unam"):
            _reetiquetar_parrafo(elem, "iijunam", texto_limpio)
            contenido.como_citar.append(str(elem))
            continue
        if fase == "como_citar" and texto_lower == "apa":
            _reetiquetar_parrafo(elem, "APA", texto_limpio)
            contenido.como_citar.append(str(elem))
            continue

        if fase != "como_citar" and ("referencias" in clases or "bib" in clases.split()):
            contenido.referencias.append(str_elem)
            fase = "referencias"
            continue

        # --- INICIO BLOQUE: DECLARACIONES ÉTICAS, IA Y AGRADECIMIENTOS ---
        es_declaracion_etica_titulo = False
        kw_titulos_etica = [
            "declaración de uso de ia", "declaracion de uso de ia", 
            "conflicto de intereses", "declaración de conflicto de intereses", "declaracion de conflicto de intereses", 
            "autoría", "autoria", "agradecimientos", "agradecimiento",
            "declaration of ai use", "ai use declaration", 
            "conflict of interest", "declaration of interest", "declaration of interests", 
            "authorship", "acknowledgment", "acknowledgments", "acknowledgement", "acknowledgements",
            "declaração de uso de ia", "declaracao de uso de ia", 
            "conflito de interesses", "declaração de conflito de interesses", "declaracao de conflito de interesses", 
            "autoria", "agradecimentos", "agradecimento",
            "déclaration d'utilisation de l'ia", "declaration d'utilisation de l'ia", 
            "conflit d'intérêts", "conflit d'interets", "déclaration de conflit d'intérêts", "declaration de conflit d'interets", 
            "qualité d'auteur", "qualite d'auteur", "remerciements", "remerciement"
        ]
        
        if fase != "como_citar" and texto_limpio and _es_titulo_declaracion(elem, texto_lower, kw_titulos_etica):
            es_declaracion_etica_titulo = True
        
        if es_declaracion_etica_titulo:
            if contenido.declaraciones_etica:
                contenido.declaraciones_etica.append('<hr class="HorizontalRule-1" />')
            elem.name = "h4"
            elem["class"] = ["declaracion_titulo"]
            contenido.declaraciones_etica.append(str(elem))
            fase = "declaraciones"
            continue
        # --- FIN BLOQUE ---

        if "como_citar" in clases or "iijunam" in clases or "apa" in clases.split():
            contenido.como_citar.append(str_elem)
            fase = "como_citar"
            continue

        if fase == "declaraciones":
            if texto_limpio or elem.name in ["table", "img", "hr"]:
                if elem.name == "p":
                    elem["class"] = ["declaracion_texto"]
                contenido.declaraciones_etica.append(str(elem))
            continue

        if fase == "como_citar":
            if elem.name == "hr":
                fase = "cuerpo" 
            else:
                contenido.como_citar.append(str_elem)
            continue

        if texto_limpio or elem.name in ["table", "img", "hr"] or elem.find("img"):
            # CORRECCIÓN: Transformar elementos con clase de InDesign a etiquetas semánticas
            if "subarabigos" in clases:
                elem.name = "h5"
                elem["class"] = ["subarabigos"]
                str_elem = str(elem)
            elif "romanos" in clases:
                elem.name = "h3"
                elem["class"] = ["romanos"]
                str_elem = str(elem)
            elif "arabigos" in clases:
                elem.name = "h4"
                elem["class"] = ["arabigos"]
                str_elem = str(elem)
            elif elem.name == "table":
                str_elem = f'<div class="table-responsive">\n{elem}\n</div>'
                
            contenido.secciones_cuerpo.append(str_elem)

    if autor_actual:
        contenido.autores_obj.append(autor_actual)

    seccion_notas = soup.find("section", class_="_idFootnotes")
    if seccion_notas:
        contenido.notas_html = str(seccion_notas)

    return contenido

def generar_html_referencia(contenido: ContenidoArticulo, css_inline: str, nombre_revista: str) -> str:
    css_tags = f"<style>\n{css_inline}\n\t\t</style>"
    
    ids = _generar_identificadores_cc(contenido, nombre_revista)
    id_lines = []
    for i, ident in enumerate(ids):
        if i < len(ids) - 1:
            id_lines.append(f'<br>{ident}')
        else:
            id_lines.append(f'<br>{ident}<br><br>')
    identificadores_html = f'<p class="notas_iniciales">\n\t\t\t{"".join(id_lines)}\n\t\t</p>'
    separador_identificadores = '\n\t\t<hr class="HorizontalRule-1" />'
    
    ORCID_SVG = """<a href="{url}" target="_blank" style="text-decoration: none; margin-left: 5px;"><span class="_idSVGInline" style="display: inline-block; width: 1em; height: 1em; vertical-align: middle;"><svg version="1.1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" style="width: 100%; height: 100%; display: block;"><style type="text/css">.st0{fill:#A6CE39;}.st1{fill:#FFFFFF;}</style><circle class="st0" cx="128" cy="128" r="128"/><g><path class="st1" d="M86.3,186.2H70.9V79.1h15.4v48.4V186.2z"/><path class="st1" d="M108.9,79.1h41.6c39.6,0,57,28.3,57,53.6c0,27.5-21.5,53.6-56.8,53.6h-41.8V79.1z M124.3,172.4h24.5c34.9,0,42.9-26.5,42.9-39.7c0-21.5-13.7-39.7-43.7-39.7h-23.7V172.4z"/><path class="st1" d="M88.7,56.8c0,5.5-4.5,10.1-10.1,10.1c-5.6,0-10.1-4.6-10.1-10.1c0-5.6,4.5-10.1,10.1-10.1C84.2,46.7,88.7,51.3,88.7,56.8z"/></g></svg></span></a>"""
    
    autores_html_list = []
    for autor in contenido.autores_obj:
        orcid_str = ORCID_SVG.replace("{url}", autor.orcid_url) if autor.orcid_url else ""
        autores_html_list.append(f'<p class="AUT-DOS-NOMBRES">{autor.nombre_html}{orcid_str}</p>')
        for adscripcion in autor.adscripciones_html:
            autores_html_list.append(f'<p class="nota-de-autor-final">{adscripcion}</p>')
            
    autores_html = _indentar_html(autores_html_list, 4)

    bloques_post = []

    if contenido.declaraciones_etica or contenido.fechas or contenido.como_citar or contenido.notas_html:
        bloques_post.append('<hr class="HorizontalRule-1" />')

    if contenido.declaraciones_etica:
        bloques_post.extend(contenido.declaraciones_etica)
        if contenido.fechas or contenido.como_citar or contenido.notas_html:
            bloques_post.append('<hr class="HorizontalRule-1" />')

    if contenido.fechas:
        fechas_unidas = "<br>\n\t\t\t\t".join(f for f in contenido.fechas if f)
        bloques_post.append(f'<p class="recepcion">{fechas_unidas}</p>')
        bloques_post.append('<hr class="HorizontalRule-1" />')

    if contenido.como_citar:
        como_citar_unidas = "\n\t\t\t\t".join(contenido.como_citar)
        bloques_post.append(f'<div class="como_citar_section">\n\t\t\t\t\t{como_citar_unidas}\n\t\t\t\t</div>')
        bloques_post.append('<hr class="HorizontalRule-1" />')

    if contenido.notas_html:
        bloques_post.append(contenido.notas_html)

    post_html = _indentar_html(bloques_post, 4)
    cuerpo_html = _indentar_html(contenido.secciones_cuerpo, 4)
    referencias_html = _indentar_html(contenido.referencias, 4)

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
\t\t\t<div class="Marco-de-texto-b-sico">
\t\t\t\t<p class="body_text2"><span>{contenido.tipo_articulo}</span></p>
\t\t\t</div>
\t\t\t{identificadores_html}
\t\t\t{separador_identificadores}
\t\t\t<div id="_idContainer002" class="_idGenObjectStyleOverride-1">
\t\t\t\t{contenido.titulo_es}
\t\t\t\t{contenido.titulo_en}
\t\t\t\t{autores_html}
\t\t\t\t{contenido.resumen}
\t\t\t\t{contenido.palabras_clave}
\t\t\t\t{contenido.abstract}
\t\t\t\t{contenido.keywords}
\t\t\t\t{cuerpo_html}
\t\t\t\t{referencias_html}
\t\t\t\t{post_html}
\t\t\t</div>
\t\t</div>
\t</body>
</html>"""

    html = re.sub(r'\n\s*\n', '\n', html)
    return html

def _corregir_rutas_imagenes(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for imagen in soup.find_all("img", src=True):
        src = urllib.parse.unquote(imagen["src"])
        if "web-resources/" not in src:
            continue
        nombre = src.split("web-resources/", 1)[1].split("/")[-1]
        nombre = unicodedata.normalize('NFKD', nombre).encode('ASCII', 'ignore').decode('utf-8')
        imagen["src"] = re.sub(r"[^\w\.-]", "_", nombre)
    return str(soup)

def procesar_html(html_path: str, css_inline: str, ruta_salida_html: str, nombre_revista: str, tipo_articulo_forzado: Optional[str] = None) -> bool:
    try:
        contenido = extraer_contenido(html_path)
        if tipo_articulo_forzado:
            contenido.tipo_articulo = tipo_articulo_forzado
            
        html_final = generar_html_referencia(contenido, css_inline, nombre_revista)
        html_final = _corregir_rutas_imagenes(html_final)
        html_final = re.sub(r'href="[^"#]*\.html(#[^"]+)"', r'href="\1"', html_final)
        
        with open(ruta_salida_html, "w", encoding="utf-8") as f:
            f.write(html_final)
        return True
    except Exception as e:
        print(f"    ✗ Error procesando HTML CC: {e}")
        return False