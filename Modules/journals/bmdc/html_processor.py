"""
Módulo para extraer y reestructurar HTML específico de BMDC.
Genera la estructura semántica correcta asignando las clases que permitirán 
al CSS manipular los tamaños y aplicar el espaciado correcto entre autores.
"""

import re
import urllib.parse
import unicodedata
from typing import List, Optional
from dataclasses import dataclass, field
from bs4 import BeautifulSoup, Tag

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
    fechas: List[str] = field(default_factory=list)
    como_citar: List[str] = field(default_factory=list)
    notas_html: str = ""
    doi_extraido: str = ""

def _obtener_html_interno(elemento: Tag) -> str:
    return "".join(str(child) for child in elemento.children) if elemento else ""

def _indentar_html(lista_html: List[str], tabs: int) -> str:
    if not lista_html: return ""
    espaciado = "\n" + ("\t" * tabs)
    return espaciado.join(item.replace("\n", espaciado) for item in lista_html)

def _activar_enlaces_html(elem: Tag):
    """
    Busca texto plano que sea una URL y lo envuelve en una etiqueta <a>.
    Ignora el texto que ya está dentro de un enlace.
    """
    # Usamos list() para evitar errores al modificar el árbol mientras lo iteramos
    for text_node in list(elem.find_all(string=True)):
        if text_node.parent and text_node.parent.name == 'a': 
            continue
        
        texto = str(text_node)
        if "http://" in texto or "https://" in texto:
            # Encuentra la URL y evita capturar puntos o comas finales (comunes en formato APA)
            nuevo_html = re.sub(
                r'(https?://[^\s<>"\'\\]+?(?=[.,;)]?(?:\s|<|$)))', 
                r'<a href="\1">\1</a>', 
                texto
            )
            # Si hubo un cambio, reemplazamos el nodo de texto con el nuevo HTML parseado
            if nuevo_html != texto:
                text_node.replace_with(BeautifulSoup(nuevo_html, "html.parser"))

def _extraer_url_doi(texto: str) -> str:
    match = re.search(r"(https?://(?:dx\.)?doi\.org/[^\s<>\"']+)", texto.replace(" ", ""), re.IGNORECASE)
    if not match: match = re.search(r"(10\.\d{4,9}/[-._;()/:A-Z0-9]+)", texto.replace(" ", ""), re.IGNORECASE)
    if not match: return ""
    url = match.group(1).rstrip(".,;<>\"'")
    url = url if url.startswith("http") else "https://doi.org/" + url
    return url.replace("10.22201/iij/", "10.22201/iij.")

def _generar_identificadores_bmdc(contenido: ContenidoArticulo, nombre_revista: str) -> List[str]:
    revista_id = str(nombre_revista.split('_')[0])
    vol_num = "[Vol(Núm)]"
    meses_ano = "[Meses de Año]"
    e_id = f"e{revista_id}"
    doi_html = '<span class="hipervinculo">[colocar doi aquí]</span>'

    for cita in contenido.como_citar:
        texto_plano = BeautifulSoup(cita, "html.parser").get_text()
        if "Boletín Mexicano de Derecho Comparado" in texto_plano or "BMDC" in texto_plano:
            vol_match = re.search(r'vol\.?\s*(\d+)', texto_plano, re.IGNORECASE)
            num_match = re.search(r'(?:n[úu]m(?:ero)?\.?|no\.)\s*(\d+)', texto_plano, re.IGNORECASE)
            # Cubrir rangos de meses en español e inglés:
            #   "enero-abril de 2026", "January-April, 2026", "enero-abril 2026"
            # Exigimos ≥3 letras para no capturar prefijos de e-IDs (ej. "e2052")
            # La coma opcional cubre el formato inglés "Month-Month, YYYY"
            mes_match = re.search(
                r'([a-záéíóúüñA-Z]{3,}(?:\s*[-–]\s*[a-záéíóúüñA-Z]{3,})?\s*,?\s*(?:de\s*)?\d{4})',
                texto_plano, re.IGNORECASE
            )
            # e_id: buscar "eNNNNN" fuera de URLs (eliminar URLs antes del match)
            texto_sin_urls = re.sub(r'https?://\S+', '', texto_plano)
            eid_match = re.search(r'\b(e\d{5,6})\b', texto_sin_urls, re.IGNORECASE)

            if vol_match and num_match: vol_num = f"{vol_match.group(1)}({num_match.group(1)})"
            if mes_match: meses_ano = mes_match.group(1).strip()
            if eid_match: e_id = eid_match.group(1).strip()
                
            matches_doi = re.findall(r"(https?://(?:dx\.)?doi\.org/[^\s<>\"']+)", texto_plano, re.IGNORECASE)
            if matches_doi:
                doi_url = matches_doi[0].rstrip(".,;<>\"'").replace("10.22201/iij/", "10.22201/iij.")
                doi_html = f'<a href="{doi_url}"><span class="hipervinculo">{doi_url}</span></a>'
            break

    if not '<a' in doi_html and contenido.doi_extraido:
        doi_html = f'<a href="{contenido.doi_extraido}"><span class="hipervinculo">{contenido.doi_extraido}</span></a>'

    line1 = f"Boletín Mexicano de Derecho Comparado, {vol_num}, {meses_ano}, {e_id}"
    line2 = f'e-ISSN: 2448-4873  DOI: {doi_html}'
    line3 = 'Esta obra está bajo una <a href="https://creativecommons.org/licenses/by/4.0/"><span class="hipervinculo">Licencia Creative Commons Reconocimiento 4.0 Internacional</span></a>'
    line4 = 'Instituto de Investigaciones Jurídicas de la Universidad Nacional Autónoma de México'

    return [line1, line2, line3, line4]

def extraer_contenido(html_path: str) -> ContenidoArticulo:
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
        
    for br in soup.find_all("br"): br.replace_with(" ")
    
    # Destrucción agresiva de estilos de InDesign incrustados en etiquetas
    for tag in soup.find_all(True):
        if tag.has_attr('style'):
            cleaned_style = re.sub(r'(font-size|text-indent|text-align|margin[-a-z]*|font-family|line-height)\s*:[^;]+;?', '', tag['style'], flags=re.IGNORECASE)
            if not cleaned_style.strip():
                del tag['style']
            else:
                tag['style'] = cleaned_style
                
    for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div']):
        for text_node in p.find_all(string=True):
            if text_node.parent.name in ['style', 'script']: continue
            nuevo_texto = text_node.replace('\xad', '').replace('\u200b', '').replace('\n', ' ')
            nuevo_texto = re.sub(r'\s+', ' ', nuevo_texto)
            if text_node != nuevo_texto: text_node.replace_with(nuevo_texto)

    for p in soup.find_all('p'):
        if not p.get_text(strip=True) and not p.find(['img', 'table', 'span']): p.decompose()

    for span in soup.find_all("span", class_="no-separar"): span.unwrap()
    
    # Destrucción selectiva: solo logos de InDesign y el ícono ORCID.
    # Las imágenes reales del artículo (mapas, figuras, gráficas) se preservan.
    # El ícono ORCID se elimina SOLO como <img>; el <a href> y el texto URL del span padre
    # permanecen intactos para que el loop principal pueda extraer la URL del ORCID.
    for img in soup.find_all("img"):
        src_lower = img.get("src", "").lower()
        if "logo_findearticulo" in src_lower or "logo_cc_fin" in src_lower:
            # Destruir el párrafo completo que contiene el logo basura
            parent_p = img.find_parent("p")
            if parent_p:
                parent_p.decompose()
            else:
                img.decompose()
        elif "orcid" in src_lower:
            # Solo eliminar el <img> del ícono ORCID; preservar el <a href> y el texto URL
            img.decompose()
            
    contenido = ContenidoArticulo()
    container = soup.find("div", class_="_idGenObjectStyleOverride-1") or soup.body
    if not container: return contenido
        
    elementos = [e for e in container.children if isinstance(e, Tag)]
    fase = "inicio"
    autor_actual: Optional[Autor] = None
    capturando_fecha_fragmentada = False

    for elem in elementos:
        clases = " ".join(elem.get("class", [])).lower()
        clases_limpias = clases.replace("-", " ").replace("_", " ").split()
        texto_limpio = elem.get_text(strip=False).strip()
        texto_lower = texto_limpio.lower()
        str_elem = str(elem)

        if elem.name == "section" and "_idfootnotes" in clases: continue
        if "doi" in clases_limpias or texto_lower.startswith("doi:"):
            contenido.doi_extraido = _extraer_url_doi(texto_limpio)
            continue

        is_date_class = "recepcion" in clases_limpias or "aceptacion" in clases_limpias or "aceptacion-publicacion" in clases
        # CRÍTICO: solo detectar keyword de fecha si aparece al INICIO del texto (primeros 35 chars).
        # Esto evita que párrafos del cuerpo que mencionan "publicación" o "aprobación" en medio
        # del texto sean clasificados erróneamente como fechas.
        texto_inicio = texto_lower[:35]
        has_date_kw = bool(re.search(r'^(recepci[óo]n|recibido|aceptaci[óo]n|aceptado|publicaci[óo]n|publicado|aprobaci[óo]n|aprobado)\s*:', texto_inicio))
        has_digits = bool(re.search(r'\d', texto_lower))
        is_email_or_inst = "@" in texto_lower or "universidad" in texto_lower or "instituto" in texto_lower or "facultad" in texto_lower

        # Una vez en el cuerpo del artículo, NUNCA reclasificar como fecha
        es_fecha = False
        if fase != "cuerpo":
            es_fecha = is_date_class and not is_email_or_inst
            # Para keyword-based detection: el texto debe ser corto (< 80 chars) Y empezar con la keyword
            if not es_fecha and has_date_kw and len(texto_limpio) < 80 and not is_email_or_inst:
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
            # Solo absorber si el elemento NO tiene una clase de cuerpo reconocida.
            # Esto evita que párrafos de introducción cortos con números (ej. "2024")
            # o notas de imagen (ej. "Fuente: INEGI (2023)") sean absorbidos como fechas.
            clases_cuerpo = {"pp", "body", "text", "trp", "trs", "trul", "trun",
                            "balap", "balas", "balaul", "fuente", "nota", "pie"}
            tiene_clase_cuerpo = any(c in clases_limpias for c in clases_cuerpo)
            tiene_imagen = bool(elem.find("img"))
            if not tiene_clase_cuerpo and not tiene_imagen:
                if contenido.fechas: contenido.fechas[-1] += " " + texto_limpio
                capturando_fecha_fragmentada = False
                continue
            else:
                capturando_fecha_fragmentada = False
        else:
            capturando_fecha_fragmentada = False

        if ("titulo_espanol" in clases or "titulo" in clases_limpias) and "ingles" not in clases:
            if not contenido.titulo_es:
                if elem.name != "h1": elem.name = "h1"
                elem['class'] = ['titulo_espanol']
                contenido.titulo_es = str(elem)
            continue
            
        if "titulo_ingles" in clases or "subtitulo" in clases_limpias:
            if not contenido.titulo_en:
                if elem.name != "h2": elem.name = "h2"
                elem['class'] = ['titulo_ingles']
                contenido.titulo_en = str(elem)
            continue

        # Detección de "párrafo de estilo genérico de InDesign" que corresponde al primer autor.
        # InDesign a veces exporta el primer autor con clase "Estilo-de-p-rrafo-N" en lugar de AUT.
        # Se detecta si: (a) aún estamos en fase "inicio", (b) no hay autor_actual todavía,
        # (c) la clase contiene "estilo-de-p" o "estilo de p" (variante de InDesign), y
        # (d) el texto NO parece un título, fecha, institución ni resumen.
        es_parrafo_estilo_indesign = (
            fase == "inicio"
            and autor_actual is None
            and re.search(r'estilo.de.p', clases, re.IGNORECASE)
            and not is_date_class
            and not is_email_or_inst
            and "resumen" not in clases
            and "abstract" not in clases
            and len(texto_limpio) < 120
        )

        es_autor = (
            "aut-dos-nombres" in clases
            or "aut_dos_nombres" in clases
            or es_parrafo_estilo_indesign
            or (
                "aut" in clases_limpias
                and "autor" not in clases_limpias
                and "nota" not in clases_limpias
                and "resumen" not in clases
                and "abstract" not in clases
            )
            or "autor" in clases_limpias and "nota" not in clases_limpias
        )
        if es_autor:
            if autor_actual: contenido.autores_obj.append(autor_actual)
            autor_actual = Autor(nombre_html=_obtener_html_interno(elem))
            continue
            
        if "orcid" in clases_limpias:
            if autor_actual:
                # 1) Buscar <a href> explícito (algunos artículos lo tienen)
                enlace = elem.find("a", href=True)
                if enlace and "orcid.org" in enlace.get("href", "").lower():
                    autor_actual.orcid_url = enlace["href"].strip()
                else:
                    # 2) Fallback: extraer URL de texto plano del span/párrafo
                    #    (caso BMDC: <span class="hipervinculo"><img/> https://orcid.org/...</span>)
                    match = re.search(r"(https?://orcid\.org/[\d\-X]+)", texto_limpio)
                    if match:
                        autor_actual.orcid_url = match.group(1).strip()
                    elif enlace:
                        # 3) Cualquier <a href> como último recurso
                        autor_actual.orcid_url = enlace["href"].strip()
            continue

        if fase == "inicio" and autor_actual and ("nota-de-autor" in clases or "adscripcion" in clases or "correo" in clases or "@" in texto_limpio or "universidad" in texto_lower or "instituto" in texto_lower or "facultad" in texto_lower):
            if len(texto_limpio) < 200: 
                autor_actual.adscripciones_html.append(_obtener_html_interno(elem))
                continue

        # Clasificación segura para resúmenes
        if ("resumen" in clases and "resumen_ingles" not in clases) or texto_lower.startswith("resumen:"):
            elem['class'] = ['resumen']; contenido.resumen = str(elem); fase = "cuerpo"; continue
        if "palabras-clave" in clases or texto_lower.startswith("palabras clave:"):
            elem['class'] = ['palabras-clave']; contenido.palabras_clave = str(elem); fase = "cuerpo"; continue
        if "resumen_ingles" in clases or texto_lower.startswith("abstract:"):
            elem['class'] = ['resumen_ingles']; contenido.abstract = str(elem); fase = "cuerpo"; continue
        if "keywords" in clases or "keyword" in clases_limpias or texto_lower.startswith("keywords:"):
            elem['class'] = ['keywords']; contenido.keywords = str(elem); fase = "cuerpo"; continue

        # Priorizar "cómo citar" para evitar que sea tratado como referencia
        is_como_citar = "como_citar" in clases or "iijunam" in clases_limpias or "apa" in clases_limpias or texto_lower == "cómo citar"
        if is_como_citar:
            elem['class'] = ['como_citar']
            _activar_enlaces_html(elem) # Transformamos el texto en un enlace real
            contenido.como_citar.append(str(elem))
            fase = "como_citar"
            continue
            
        if fase == "como_citar":
            if elem.name == "hr": 
                fase = "cuerpo" 
            else: 
                _activar_enlaces_html(elem) # Transformamos el texto en un enlace real
                contenido.como_citar.append(str(elem)) # Usamos str(elem) en vez de str_elem para capturar el cambio
            continue

        # Procesamiento estricto y encapsulado de Referencias
        is_referencia_heading = False
        if re.search(r'\b(referencias|bibliografía|bibliografia)\b', texto_lower) and len(texto_limpio) < 80:
            is_referencia_heading = True
            
        es_referencia = False
        if is_referencia_heading or any(x in clases_limpias for x in ["referencias", "bibliografia", "bib", "bibliografía"]):
            es_referencia = True
        elif fase == "referencias":
            if elem.name not in ["hr", "section"]:
                es_referencia = True

        if es_referencia:
            # Si es el título de la sección de referencias
            if is_referencia_heading:
                elem.name = "h3"
                elem['class'] = ['romanos']
                if elem.has_attr('style'): del elem['style']
                for child in elem.find_all(True):
                    if child.has_attr('style'): del child['style']
                contenido.referencias.append(str(elem))
                fase = "referencias"
                continue

            # Si es la referencia propiamente
            elem.name = "p"
            elem['class'] = ['referencias']
            
            # Destrucción TOTAL de modificadores visuales (texto plano exigido)
            for tag in elem.find_all(['strong', 'b', 'em', 'i']): 
                tag.unwrap()
            
            if elem.has_attr('style'): del elem['style']
            for child in elem.find_all(True):
                if child.has_attr('style'): del child['style']
                # Eliminamos clases residuales salvo aquellas que formen una liga explícita
                if child.has_attr('class'):
                    c_str = " ".join(child['class']).lower()
                    if not any(x in c_str for x in ['hipervinculo', 'link']):
                        del child['class']

            contenido.referencias.append(str(elem))
            fase = "referencias"
            continue

        # Cuerpo del documento (Todo lo demás)
        # Incluir párrafos que solo contienen una imagen (texto_limpio vacío pero tienen <img>)
        tiene_imagen_real = bool(elem.find("img"))
        if texto_limpio or elem.name in ["table", "img", "hr"] or tiene_imagen_real:
            if elem.name == "table":
                str_elem = f'<div class="table-responsive">\n{elem}\n</div>'
            else:
                is_heading = False

                # Coincidencia EXACTA con clases de encabezado para evitar falsos positivos
                if any(x in clases_limpias for x in ["romano", "arabigo", "seccion", "vv", "romanos", "arabigos"]):
                    is_heading = True
                elif len(texto_limpio) < 150 and elem.name in ["p", "h1", "h2", "h3", "h4"]:
                    if (re.match(r'^(I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII|XIII|XIV|XV)\.?\s+', texto_limpio)
                            or re.match(r'^\d+\.\s+', texto_limpio)
                            or texto_lower in ["introducción", "introduccion", "conclusiones", "conclusión"]):
                        is_heading = True
                    elif elem.find("strong") and elem.get_text(strip=True) == elem.find("strong").get_text(strip=True):
                        is_heading = True

                if is_heading:
                    if (re.match(r'^(I|V|X)', texto_limpio)
                            or "romano" in clases_limpias
                            or "vv" in clases_limpias
                            or texto_lower in ["introducción", "introduccion", "conclusiones", "conclusión"]):
                        elem.name = "h3"
                        elem['class'] = ['romanos']
                    else:
                        elem.name = "h4"
                        elem['class'] = ['arabigos']

                    if elem.has_attr('style'): del elem['style']
                    for child in elem.find_all(True):
                        if child.has_attr('style'): del child['style']

                else:
                    # Normalizar clases residuales de InDesign en párrafos de cuerpo:
                    # PP (primer párrafo de sección) y BODY-text reciben clase unificada.
                    # Los párrafos que sólo contienen imagen reciben clase dedicada para
                    # alineación izquierda; los pies de figura (Fuente:...) igual.
                    clases_originales = " ".join(elem.get("class", [])).lower()
                    if tiene_imagen_real and not texto_limpio:
                        # Párrafo contenedor de imagen real: clase dedicada, sin texto
                        elem.name = "p"
                        elem['class'] = ['imagen-articulo']
                    elif tiene_imagen_real:
                        # Párrafo con imagen Y texto (poco común pero posible)
                        elem.name = "p"
                        elem['class'] = ['imagen-articulo']
                    elif "pp" in clases_limpias or "paraoverride" in clases_originales:
                        # Primer párrafo de sección (PP / ParaOverride): misma clase que BODY-text
                        # para heredar tipografía unificada
                        if not any(x in clases_originales for x in ["fuente", "pie", "caption", "mapa", "figura", "tabla"]):
                            elem.name = "p"
                            elem['class'] = ['BODY-text']
                        else:
                            elem.name = "p"
                            elem['class'] = ['pie-figura']
                    elif any(x in clases_limpias for x in ["body", "text", "estilos"]):
                        # Párrafos de cuerpo con clases compuestas de InDesign: normalizar
                        elem.name = "p"
                        elem['class'] = ['BODY-text']

                    if elem.has_attr('style'): del elem['style']
                    for child in elem.find_all(True):
                        if child.has_attr('style'): del child['style']

                str_elem = str(elem)
            contenido.secciones_cuerpo.append(str_elem)

    if autor_actual: contenido.autores_obj.append(autor_actual)
    seccion_notas = soup.find("section", class_="_idFootnotes")
    if seccion_notas: contenido.notas_html = str(seccion_notas)

    return contenido

def generar_html_referencia(contenido: ContenidoArticulo, css_inline: str, nombre_revista: str) -> str:
    css_tags = f"<style>\n{css_inline}\n\t\t</style>"
    ids = _generar_identificadores_bmdc(contenido, nombre_revista)
    id_lines = [f'<br>{ident}' if i < len(ids) - 1 else f'<br>{ident}<br><br>' for i, ident in enumerate(ids)]
    identificadores_html = f'<p class="notas_iniciales">\n\t\t\t{"".join(id_lines)}\n\t\t</p>'
    separador_identificadores = '\n\t\t<hr class="HorizontalRule-1" />'
    
    ORCID_SVG = """<span style="display:inline-block; vertical-align:middle; margin-left:6px;"><a href="{url}" target="_blank" style="text-decoration:none;"><span class="_idSVGInline" style="display:inline-block; width:16px; height:16px;"><svg viewBox="0 0 256 256" style="width:16px; height:16px;"><circle cx="128" cy="128" r="128" fill="#A6CE39"/><path d="M86.3,186.2H70.9V79.1h15.4v48.4V186.2z" fill="#FFF"/><path d="M108.9,79.1h41.6c39.6,0,57,28.3,57,53.6c0,27.5-21.5,53.6-56.8,53.6h-41.8V79.1z M124.3,172.4h24.5c34.9,0,42.9-26.5,42.9-39.7c0-21.5-13.7-39.7-43.7-39.7h-23.7V172.4z" fill="#FFF"/><path d="M88.7,56.8c0,5.5-4.5,10.1-10.1,10.1c-5.6,0-10.1-4.6-10.1-10.1c0-5.6,4.5-10.1,10.1-10.1C84.2,46.7,88.7,51.3,88.7,56.8z" fill="#FFF"/></svg></span></a></span>"""
    
    autores_html_list = []
    for autor in contenido.autores_obj:
        nombre_limpio = BeautifulSoup(autor.nombre_html, "html.parser")
        for tag in nombre_limpio.find_all(['strong', 'b', 'span', 'em']): tag.unwrap()
        nombre_final = str(nombre_limpio).strip()
        
        orcid_str = ORCID_SVG.replace("{url}", autor.orcid_url) if autor.orcid_url else ""
        
        autores_html_list.append(f'<p class="AUT-DOS-NOMBRES">{nombre_final}{orcid_str}</p>')
        
        for adscripcion in autor.adscripciones_html:
            adscripcion_limpia = re.sub(r'<br\s*/?>', '', adscripcion).strip()
            autores_html_list.append(f'<p class="nota-de-autor-final">{adscripcion_limpia}</p>')
            
    autores_html = _indentar_html(autores_html_list, 4)

    bloques_post = []
    if contenido.fechas or contenido.como_citar or contenido.notas_html: bloques_post.append('<hr class="HorizontalRule-1" />')
    if contenido.fechas:
        fechas_unidas = "<br>\n\t\t\t\t\t".join(f for f in contenido.fechas if f)
        bloques_post.append(f'<div class="bloque-fechas-inferior">\n\t\t\t\t\t<p class="recepcion">{fechas_unidas}</p>\n\t\t\t\t</div>')
        bloques_post.append('<hr class="HorizontalRule-1" />')
    if contenido.como_citar:
        como_citar_unidas = "\n\t\t\t\t\t".join(contenido.como_citar)
        bloques_post.append(f'<div class="como_citar_section">\n\t\t\t\t\t{como_citar_unidas}\n\t\t\t\t</div>')
        bloques_post.append('<hr class="HorizontalRule-1" />')
    if contenido.notas_html: bloques_post.append(contenido.notas_html)

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
    return re.sub(r'\n\s*\n', '\n', html)

def _corregir_rutas_imagenes(html: str) -> str:
    def reemplazar_y_sanitizar(match):
        nombre = unicodedata.normalize('NFKD', urllib.parse.unquote(match.group(1))).encode('ASCII', 'ignore').decode('utf-8')
        return f'src="{re.sub(r"[^\w\.-]", "_", nombre)}"'
    return re.sub(r'src="[^"]*?(?:web-resources/image/|image/)([^"]+)"', reemplazar_y_sanitizar, html)

def procesar_html(html_path: str, css_inline: str, ruta_salida_html: str, nombre_revista: str, tipo_articulo_forzado: Optional[str] = None) -> bool:
    try:
        contenido = extraer_contenido(html_path)
        if tipo_articulo_forzado: contenido.tipo_articulo = tipo_articulo_forzado
        html_final = generar_html_referencia(contenido, css_inline, nombre_revista)
        html_final = _corregir_rutas_imagenes(html_final)
        html_final = re.sub(r'href="[^"#]*\.html(#[^"]+)"', r'href="\1"', html_final)
        
        with open(ruta_salida_html, "w", encoding="utf-8") as f:
            f.write(html_final)
        return True
    except Exception as e:
        print(f"    ✗ Error procesando HTML BMDC: {e}")
        return False