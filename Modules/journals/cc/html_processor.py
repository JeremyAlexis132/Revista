"""
Módulo para extraer y reestructurar HTML específico de Cuestiones Constitucionales (CC).
"""

import re
import urllib.parse
import unicodedata
from typing import List, Optional
from dataclasses import dataclass, field
from bs4 import BeautifulSoup, Tag

@dataclass
class Autor:
    nombre: str = ""
    orcid: str = ""
    adscripcion: str = ""
    pais: str = ""

@dataclass
class ContenidoArticulo:
    identificadores: List[str] = field(default_factory=list)
    tipo_articulo: str = "Artículo"
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
    como_citar: List[str] = field(default_factory=list)
    notas_html: str = ""

def _limpiar_texto(elemento) -> str:
    return elemento.get_text(strip=False).strip() if elemento else ""

def _obtener_html_interno(elemento) -> str:
    return "".join(str(child) for child in elemento.children) if elemento else ""

def _inferir_tipo_articulo(titulo: str, texto_cuerpo: str = "") -> str:
    """Asigna el tipo de sección basado en el contenido para CC."""
    t = titulo.lower()
    if "reseña" in t or "review" in t:
        return "Reseña bibliográfica"
    if "jurisprudencial" in t:
        return "Comentario jurisprudencial"
    if "legislativ" in t:
        return "Comentario legislativo"
    
    cuerpo_head = texto_cuerpo[:500].lower()
    if "comentario jurisprudencial" in cuerpo_head:
        return "Comentario jurisprudencial"
        
    return "Artículo"

def _extraer_orcid(elemento: Tag) -> str:
    if not elemento: return ""
    enlace = elemento.find("a", href=True)
    if enlace and "orcid.org" in enlace["href"]:
        return enlace["href"].strip()
    match = re.search(r"\b\d{4}-\d{4}-\d{4}-\d{3}[\dX]\b", elemento.get_text(" ", strip=True))
    return f"https://orcid.org/{match.group(0)}" if match else ""

def _generar_identificadores_cc(contenido: ContenidoArticulo, nombre_revista: str) -> List[str]:
    revista_id = str(nombre_revista.split('_')[0])
    line1 = f"Cuestiones Constitucionales, Revista Mexicana de Derecho Constitucional, Núm. [X], e{revista_id}"
    line2 = f'e-ISSN: 2448-4881 DOI: <a href="https://doi.org/10.22201/iij.24484881e.202X.{revista_id}"><span class="Hiperv-nculo">[Colocar DOI]</span></a>'
    line3 = 'Esta obra está bajo una <a href="https://creativecommons.org/licenses/by/4.0/"><span class="Hiperv-nculo">Licencia Creative Commons Reconocimiento 4.0 Internacional</span></a>'
    return [line1, line2, line3]

def _limpiar_imagenes_finales(soup: BeautifulSoup):
    """Busca y elimina la imagen de 'fin de artículo' y sus contenedores."""
    # 1. Eliminar contenedores con la clase logo_cc_fin
    for div in soup.find_all("div", class_="logo_cc_fin"):
        # Borrar al contenedor principal del layout si existe para que no quede espacio vacío
        padre_layout = div.find_parent("div", class_="_idGenObjectLayout-1")
        if padre_layout:
            padre_layout.decompose()
        else:
            div.decompose()
            
    # 2. Eliminación de respaldo rastreando el src de la imagen directamente
    for img in soup.find_all("img"):
        src = img.get("src", "").lower()
        if "logo_findearticulo_cc" in src or "logo_cc_fin" in src:
            padre_layout = img.find_parent("div", class_="_idGenObjectLayout-1")
            if padre_layout:
                padre_layout.decompose()
            else:
                img.decompose()

def extraer_contenido(html_path: str) -> ContenidoArticulo:
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
        
    for span in soup.find_all("span", class_="no-separar"):
        span.unwrap()
        
    _limpiar_imagenes_finales(soup)
        
    contenido = ContenidoArticulo()
    
    container = soup.find("div", class_="_idGenObjectStyleOverride-1") or soup.body
    if not container: return contenido
        
    elementos = [e for e in container.children if isinstance(e, Tag)]
    
    idx = 0
    autor_actual: Optional[Autor] = None

    while idx < len(elementos):
        elem = elementos[idx]
        clases = " ".join(elem.get("class", [])).lower()
        texto_limpio = _limpiar_texto(elem)
        str_elem = f'<div class="table-responsive">\n{elem}\n</div>' if elem.name == "table" else str(elem)

        # Identificadores (Normalmente el DOI se exporta aquí)
        if "doi" in clases:
            contenido.identificadores.append(str_elem)
            idx += 1
            continue

        # Títulos
        if "titulo_espanol" in clases:
            contenido.titulo_es = _obtener_html_interno(elem)
            contenido.tipo_articulo = _inferir_tipo_articulo(contenido.titulo_es)
            idx += 1
            continue

        if "titulo_ingles" in clases:
            contenido.titulo_en = _obtener_html_interno(elem)
            idx += 1
            continue

        # Autores
        if "aut-dos-nombres" in clases or "aut" in clases.split():
            if autor_actual: 
                contenido.autores.append(autor_actual)
            autor_actual = Autor(nombre=_obtener_html_interno(elem))
            idx += 1
            continue

        if "orcid" in clases:
            if autor_actual: 
                autor_actual.orcid = _extraer_orcid(elem)
            idx += 1
            continue
            
        if "nota-de-autor-final" in clases:
            if autor_actual: 
                if autor_actual.adscripcion:
                    autor_actual.adscripcion += " | " + _limpiar_texto(elem)
                else:
                    autor_actual.adscripcion = _limpiar_texto(elem)
            idx += 1
            continue

        # Fechas
        if "recepcion" in clases or "aceptacion-publicacion" in clases:
            contenido.fechas.append(_obtener_html_interno(elem).strip())
            idx += 1
            continue

        # Resúmenes y Palabras Clave
        if "resumen" in clases and not "resumen_ingles" in clases:
            contenido.resumen = _obtener_html_interno(elem)
            idx += 1
            continue

        if "palabras-clave" in clases:
            contenido.palabras_clave = _obtener_html_interno(elem)
            idx += 1
            continue

        if "resumen_ingles" in clases:
            contenido.abstract = _obtener_html_interno(elem)
            idx += 1
            continue

        if "keywords" in clases:
            contenido.keywords = _obtener_html_interno(elem)
            idx += 1
            continue

        # Referencias y Cómo Citar
        if "referencias" in clases:
            contenido.referencias.append(str_elem)
            idx += 1
            continue
            
        if "como_citar" in clases or "iijunam" in clases or "apa" in clases.split():
            contenido.como_citar.append(str_elem)
            idx += 1
            continue

        # Cuerpo del documento
        clases_cuerpo = ["sumario", "romanos", "arabigos", "pp", "body-text", "trun"]
        if any(c in clases for c in clases_cuerpo) or elem.name in ["table", "img"]:
            contenido.secciones_cuerpo.append(str_elem)
            idx += 1
            continue
            
        # Elementos genéricos sobrantes
        if texto_limpio and elem.name not in ["hr", "br"]:
             contenido.secciones_cuerpo.append(str_elem)

        idx += 1

    if autor_actual:
        contenido.autores.append(autor_actual)

    seccion_notas = soup.find("section", class_="_idFootnotes")
    if seccion_notas:
        contenido.notas_html = str(seccion_notas)

    return contenido

def generar_html_referencia(contenido: ContenidoArticulo, css_inline: str, nombre_revista: str) -> str:
    css_tags = f"<style>\n{css_inline}\n\t\t</style>"
    
    ids = contenido.identificadores if contenido.identificadores else _generar_identificadores_cc(contenido, nombre_revista)
    id_lines = [f'<br>{i}' for i in ids]
    identificadores_html = f'\n\t\t<p class="notas_iniciales">\t\n\t\t\t{"".join(id_lines)}\n\t\t</p>'
    
    autores_html = ""
    for a in contenido.autores:
        orcid_html = f' <span class="Versalitas"><a href="{a.orcid}">[ORCID]</a></span>' if a.orcid else ""
        autores_html += f'\n\t\t\t<p class="AUT-DOS-NOMBRES">{a.nombre}{orcid_html}</p>'
        if a.adscripcion: 
            for adscripcion_part in a.adscripcion.split(" | "):
                autores_html += f'\n\t\t\t<p class="nota-de-autor-final">{adscripcion_part}</p>'

    fechas = "<br>".join(contenido.fechas)
    fechas_html = f'\n\t\t\t<hr class="HorizontalRule-1" />\n\t\t\t<p class="recepcion">{fechas}</p>' if fechas else ""
    
    resumen_es = f'\n\t\t\t<p class="resumen">{contenido.resumen}</p>' if contenido.resumen else ""
    pclave_es = f'\n\t\t\t<p class="palabras-clave">{contenido.palabras_clave}</p>' if contenido.palabras_clave else ""
    resumen_en = f'\n\t\t\t<p class="resumen_ingles" lang="en-US">{contenido.abstract}</p>' if contenido.abstract else ""
    pclave_en = f'\n\t\t\t<p class="keywords" lang="en-US">{contenido.keywords}</p>' if contenido.keywords else ""

    cuerpo = "\n\t\t\t".join(contenido.secciones_cuerpo)
    referencias = "\n\t\t\t".join(contenido.referencias)
    como_citar = "\n\t\t\t".join(contenido.como_citar)
    
    if como_citar:
        como_citar = f'\n\t\t\t<hr class="HorizontalRule-1" />\n\t\t\t<div class="como_citar_section">\n\t\t\t{como_citar}\n\t\t\t</div>'

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
{identificadores_html}
\t\t\t<hr class="HorizontalRule-1" />
\t\t\t<h1 class="titulo_espanol">{contenido.titulo_es}</h1>
\t\t\t<h2 class="titulo_ingles">{contenido.titulo_en}</h2>
{autores_html}
{fechas_html}
{resumen_es}
{pclave_es}
{resumen_en}
{pclave_en}
\t\t\t{cuerpo}
\t\t\t{referencias}
{como_citar}
\t\t\t{contenido.notas_html}
\t\t</div>
\t</body>
</html>"""

    return html

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

def procesar_html(html_path: str, css_inline: str, ruta_salida_html: str, nombre_revista: str, tipo_articulo_forzado: Optional[str] = None) -> bool:
    try:
        contenido = extraer_contenido(html_path)
        html_final = generar_html_referencia(contenido, css_inline, nombre_revista)
        html_final = _corregir_rutas_imagenes(html_final)
        html_final = re.sub(r'href="[^"#]*\.html(#[^"]+)"', r'href="\1"', html_final)
        
        with open(ruta_salida_html, "w", encoding="utf-8") as f:
            f.write(html_final)
        return True
    except Exception as e:
        print(f"    ✗ Error procesando HTML CC: {e}")
        return False