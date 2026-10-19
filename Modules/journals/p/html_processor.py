"""
Procesador de HTML para la revista Problema (módulo p).

Lee el HTML exportado por InDesign (clases "ESTILOS-FINALES_*") y lo
reestructura con el orden y la apariencia del PDF:

    Título (ES) / Título (EN)
    Autor(es) -> ORCID -> adscripción y correo (centrados)
    Fechas (a la derecha) y DOI
    Resumen + Palabras clave | Abstract + Keywords | Sumario
    Cuerpo y referencias
    Cómo citar (IIJ-UNAM / APA)
    Notas al pie

La interfaz pública (procesar_html) es la misma que la de los demás módulos.
"""

import html as _html
import re
import urllib.parse
import unicodedata
from dataclasses import dataclass, field
from typing import List, Optional

from bs4 import BeautifulSoup, Tag

_RE_PREFIJO_ESTILO = re.compile(r"^ESTILOS[-_]FINALES[-_]", re.IGNORECASE)

# estilo de párrafo (minúsculas, sin prefijo) -> etiqueta semántica
_ETIQUETAS_SEMANTICAS = {
    "tcc-1": "h1",
    "tcc-2": "h2",
    "vv": "h3",
    "ia": "h4",
    "is": "h5",
}

_KW_COMO_CITAR = ("cómo citar", "como citar", "how to cite", "comment citer")
_RE_KEYWORDS = re.compile(r"^\s*(keywords?|key\s+words|mots[\s-]*cl[eé]s?)\b", re.IGNORECASE)
# Estilos de cita en bloque (varían por número y por mayúsculas/minúsculas)
_ESTILOS_CITA_BLOQUE = {"trun", "trp", "tri", "trpu", "trunic", "trs", "trul"}
_PREFIJOS_FECHA = ("recepcion", "recepción", "aceptacion", "aceptación", "publicacion",
                   "publicación", "recibido", "aceptado", "publicado", "fecha")
_RE_ETIQUETA_FECHA = re.compile(
    r"^\s*(?:fecha\s+de\s+|date\s+(?:of\s+)?)?"
    r"(recepci[oó]n|recibido|aceptaci[oó]n|aceptado|publicaci[oó]n|publicado|received|accepted|published|submitted)\s*[:.]",
    re.IGNORECASE,
)
_RE_AUTOR_CLASE = re.compile(r"^aut(?:[-_].*)?$", re.IGNORECASE)   # AUT, AUT-simple, AUT-DOS-NOMBRES...
_RE_PALABRAS_CLAVE = re.compile(r"^\s*(palabras?[\s-]*clave|palavras?[\s-]*chave|mots[\s-]*cl[eé]s?)\s*:", re.IGNORECASE)
_RE_SUMARIO = re.compile(r"^\s*(sumario|summary|sommaire)\s*[:.]", re.IGNORECASE)
_RE_ANIO = re.compile(r"\b(?:1[89]|20)\d{2}\b")
_RE_TITULO_FIGURA = re.compile(
    r"^\s*(ilustraci[oó]n|figura|tabla|gr[aá]fic[ao]|cuadro|mapa|imagen|esquema|diagrama)\s*\d+",
    re.IGNORECASE,
)
_RE_FUENTE_FIGURA = re.compile(r"^\s*(fuente|elaboraci[oó]n propia|source)\b", re.IGNORECASE)

ORCID_SVG = (
    '<svg version="1.1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" aria-hidden="true">'
    '<circle fill="#A6CE39" cx="128" cy="128" r="128"/>'
    '<g fill="#FFFFFF">'
    '<path d="M86.3,186.2H70.9V79.1h15.4v48.4V186.2z"/>'
    '<path d="M108.9,79.1h41.6c39.6,0,57,28.3,57,53.6c0,27.5-21.5,53.6-56.8,53.6h-41.8V79.1z '
    'M124.3,172.4h24.5c34.9,0,42.9-26.5,42.9-39.7c0-21.5-13.7-39.7-43.7-39.7h-23.7V172.4z"/>'
    '<path d="M88.7,56.8c0,5.5-4.5,10.1-10.1,10.1c-5.6,0-10.1-4.6-10.1-10.1c0-5.6,4.5-10.1,10.1-10.1'
    'C84.2,46.7,88.7,51.3,88.7,56.8z"/>'
    '</g></svg>'
)


@dataclass
class Autor:
    nombre_html: str = ""
    orcid_url: str = ""
    adscripciones_html: List[str] = field(default_factory=list)


@dataclass
class ContenidoArticulo:
    tipo_articulo: str = ""
    titulo_es: str = ""
    titulo_en: str = ""
    autores_obj: List[Autor] = field(default_factory=list)
    fechas: List[str] = field(default_factory=list)
    doi_html: str = ""
    resumen: str = ""
    palabras_clave: str = ""
    abstract: str = ""
    abstract_primero: bool = False  # artículos en inglés: el Abstract va antes que el Resumen
    keywords: str = ""
    sumario: str = ""
    cuerpo: List[str] = field(default_factory=list)
    como_citar: List[str] = field(default_factory=list)
    notas_html: str = ""


# ----------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------
def _indentar_html(lista_html: List[str], tabs: int) -> str:
    if not lista_html:
        return ""
    espaciado = "\n" + ("\t" * tabs)
    return espaciado.join(item.replace("\n", espaciado) for item in lista_html)


def _texto(elem: Tag) -> str:
    return re.sub(r"\s+", " ", elem.get_text(" ", strip=True).replace("\xa0", " ")).strip()


def _extraer_url_doi(texto: str) -> str:
    compacto = texto.replace(" ", "")
    match = re.search(r"(https?://(?:dx\.)?doi\.org/[^\s<>\"']+)", compacto, re.IGNORECASE)
    if not match:
        match = re.search(r"(10\.\d{4,9}/[-._;()/:A-Z0-9]+)", compacto, re.IGNORECASE)
    if not match:
        return ""
    url = match.group(1).rstrip(".,;<>\"'")
    url = url if url.startswith("http") else "https://doi.org/" + url
    return url.replace("10.22201/iij/", "10.22201/iij.")


def _normalizar_clases(soup: BeautifulSoup) -> None:
    """Quita el prefijo ESTILOS-FINALES_ y convierte títulos/encabezados a h1..h5."""
    for tag in soup.find_all(True):
        clases = tag.get("class")
        if not clases:
            continue
        nuevas = [_RE_PREFIJO_ESTILO.sub("", c) for c in clases]
        tag["class"] = nuevas
        if tag.name == "p":
            for c in nuevas:
                destino = _ETIQUETAS_SEMANTICAS.get(c.lower())
                if destino is None and re.match(r"^tcc-[12]\b", c.lower()):
                    # variantes del estilo de título (p. ej. TCC-1_resena)
                    destino = "h1" if c.lower().startswith("tcc-1") else "h2"
                if destino:
                    tag.name = destino
                    break


def _limpiar_soup(soup: BeautifulSoup) -> None:
    # "no-separar" es solo una marca de InDesign: si el span trae otro estilo
    # (p. ej. CharOverride-2 con tamaño de letra) se conserva y solo se quita la marca.
    for span in soup.find_all("span", class_="no-separar"):
        otras = [c for c in span.get("class", []) if c != "no-separar"]
        if otras:
            span["class"] = otras
        else:
            span.unwrap()
    for ancla in soup.find_all("a", id=re.compile(r"^_idTextAnchor")):
        if not ancla.get_text(strip=True) and not ancla.find(True):
            ancla.decompose()
    _normalizar_clases(soup)


def _neutralizar_br(elem: Tag) -> None:
    """Los saltos de línea forzados de los títulos se vuelven espacios."""
    for br in elem.find_all("br"):
        br.replace_with(" ")


def _clases(elem: Tag) -> List[str]:
    return list(elem.get("class") or [])


def _agregar_clase(elem: Tag, *nuevas: str) -> None:
    elem["class"] = _clases(elem) + [n for n in nuevas if n not in _clases(elem)]


_RE_ORCID_ID = re.compile(r"(\d{4})-(\d{4})-(\d{4})-(\d{3}[\dXx])")


def _extraer_orcid(elem: Tag) -> str:
    """
    URL de ORCID de un párrafo, venga como enlace, como texto plano o solo como ID
    (0000-0000-0000-000X). Devuelve "" si no hay.
    """
    for a in elem.find_all("a", href=True):
        if "orcid" in a["href"].lower():
            url = re.sub(r"\s+", "", a["href"])
            if url:
                return url
    compacto = re.sub(r"\s+", "", elem.get_text("", strip=True))
    match = _RE_ORCID_ID.search(compacto)
    if match:
        return "https://orcid.org/" + "-".join(match.groups()).upper()
    return ""


def _html_orcid(autor: Autor) -> str:
    if not autor.orcid_url:
        return ""
    url = _html.escape(autor.orcid_url, quote=True)
    return (
        f'<p class="orcid"><a class="orcid-icono" href="{url}" target="_blank" '
        f'rel="noopener" aria-label="ORCID">{ORCID_SVG}</a>'
        f'<a href="{url}" target="_blank" rel="noopener">{_html.escape(autor.orcid_url)}</a></p>'
    )


# ----------------------------------------------------------------------
# Extracción
# ----------------------------------------------------------------------
def extraer_contenido(html_path: str) -> ContenidoArticulo:
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    _limpiar_soup(soup)

    contenedor = soup.find("div", class_="_idGenObjectStyleOverride-1") or soup.body or soup
    contenido = ContenidoArticulo()

    autor_actual: Optional[Autor] = None
    zona_autor = False  # True mientras se leen los párrafos que siguen a un autor
    en_como_citar = False
    ultimo_fue_figura = False

    hijos = [e for e in contenedor.children if isinstance(e, Tag)]
    bloque_resumen: Optional[str] = None  # "resumen" | "abstract" mientras se leen sus párrafos

    for i, elem in enumerate(hijos):
        clases = _clases(elem)
        clases_lower = [c.lower() for c in clases]
        texto = _texto(elem)

        # --- notas al pie ---
        if elem.name == "section" and "_idFootnotes" in clases:
            contenido.notas_html = str(elem)
            continue

        # --- elementos que no son párrafo/encabezado ---
        if elem.name == "table":
            wrapper = soup.new_tag("div", attrs={"class": "table-responsive"})
            elem.wrap(wrapper)
            contenido.cuerpo.append(str(wrapper))
            ultimo_fue_figura = True
            continue
        if elem.name not in ("p", "h1", "h2", "h3", "h4", "h5", "h6"):
            if texto or elem.find(["img", "table"]):
                contenido.cuerpo.append(str(elem))
            continue

        # --- vacíos ---
        if not texto and not elem.find("img"):
            continue
        if elem.name in ("h3", "h4", "h5"):
            zona_autor = False
            bloque_resumen = None

        # --- títulos ---
        if elem.name == "h1":
            _neutralizar_br(elem)
            contenido.titulo_es = str(elem)
            continue
        if elem.name == "h2":
            _neutralizar_br(elem)
            contenido.titulo_en = str(elem)
            continue

        # --- autor(es) ---
        if any(_RE_AUTOR_CLASE.match(c) for c in clases_lower):
            zona_autor = True
            autor_actual = Autor(nombre_html=_html_interno(elem))
            contenido.autores_obj.append(autor_actual)
            continue
        es_orcid = "orcid" in clases_lower or (
            zona_autor and elem.name == "p" and len(texto) < 120
            and ("orcid" in texto.lower() or _RE_ORCID_ID.search(texto.replace(" ", "")))
        )
        if es_orcid:
            url = _extraer_orcid(elem)
            if autor_actual is None:
                autor_actual = Autor()
                contenido.autores_obj.append(autor_actual)
            autor_actual.orcid_url = url
            continue
        if "adscripcion_mail" in clases_lower:
            if autor_actual is None:
                autor_actual = Autor()
                contenido.autores_obj.append(autor_actual)
            autor_actual.adscripciones_html.append(str(elem))
            continue

        # --- fechas y DOI ---
        # El DOI se reconoce por su contenido: en algunos números InDesign lo exporta
        # con el estilo de las fechas (recibido-y-aceptado) en lugar del estilo DOI.
        en_encabezado = (
            not contenido.resumen and not contenido.abstract
            and not contenido.cuerpo and not en_como_citar
        )
        es_doi = "doi" in clases_lower or (
            elem.name == "p" and en_encabezado and len(texto) < 200 and (
                re.match(r"^\s*doi\b", texto, re.IGNORECASE)
                or (not contenido.doi_html and "doi.org" in texto.lower())
            )
        )
        es_fecha = (
            elem.name == "p" and len(texto) < 120 and en_encabezado and (
                _RE_ETIQUETA_FECHA.match(texto)
                # por estilo, pero solo si el texto parece fecha (hay estilos de fecha
                # reutilizados para otras cosas, p. ej. un epígrafe)
                or (
                    ("recibido-y-aceptado" in clases_lower
                     or any(c.startswith(_PREFIJOS_FECHA) for c in clases_lower))
                    and _RE_ANIO.search(texto)
                )
            )
        )
        if es_fecha and not es_doi:
            zona_autor = False
            contenido.fechas.append(str(elem))
            continue
        if es_doi:
            zona_autor = False
            url = _extraer_url_doi(texto)
            if url:
                u = _html.escape(url, quote=True)
                contenido.doi_html = f'<p class="DOI">DOI: <a href="{u}">{_html.escape(url)}</a></p>'
            else:
                contenido.doi_html = f'<p class="DOI">{_html_interno(elem).strip()}</p>'
            continue

        # --- Sumario: por estilo o por su etiqueta (en artículos en inglés viene como "Summary:"
        #     con el estilo del resumen) ---
        if "sumario" in clases_lower or (
            elem.name == "p" and not en_como_citar and len(texto) < 1200 and _RE_SUMARIO.match(texto)
            and not any(_RE_ENCABEZADO.match(b) for b in contenido.cuerpo)  # aún no empieza el texto
        ):
            zona_autor = False
            bloque_resumen = None
            elem["class"] = ["SUMARIO"]  # mismo aspecto que el Sumario normal (centrado)
            contenido.sumario = str(elem)
            continue

        # --- resúmenes ---
        if clases_lower and any(c in clases_lower for c in ("resumen", "resumen_ingles", "palabras-clave", "keywords", "sumario")):
            zona_autor = False
        # Continuación del resumen/abstract: InDesign la exporta con otro estilo
        # (p. ej. resumen_seg), uno por párrafo adicional.
        es_continuacion = any(c.startswith(("resumen_seg", "resumen-seg", "abstract_seg")) for c in clases_lower)
        if es_continuacion and bloque_resumen is None:
            bloque_resumen = "resumen" if not contenido.abstract else "abstract"
        if es_continuacion or (
            bloque_resumen and elem.name == "p"
            and not any(c in clases_lower for c in ("resumen", "resumen_ingles", "palabras-clave", "keywords", "sumario"))
            and _cierra_bloque_resumen(hijos, i)
        ):
            _agregar_clase(elem, "resumen_seg")
            if bloque_resumen == "abstract":
                contenido.abstract += "\n" + str(elem)
            else:
                contenido.resumen += "\n" + str(elem)
            continue
        if "resumen" in clases_lower:
            contenido.resumen = str(elem)
            bloque_resumen = "resumen"
            continue
        if "resumen_ingles" in clases_lower:
            if not contenido.resumen:
                contenido.abstract_primero = True
            contenido.abstract = str(elem)
            bloque_resumen = "abstract"
            continue
        es_kw_pc = elem.name == "p" and en_encabezado and len(texto) < 600 and (
            _RE_KEYWORDS.match(texto) or _RE_PALABRAS_CLAVE.match(texto)
        )
        if "palabras-clave" in clases_lower or "keywords" in clases_lower or es_kw_pc:
            bloque_resumen = None
            zona_autor = False
            es_ingles = bool(_RE_KEYWORDS.match(texto)) or (
                "keywords" in clases_lower and not _RE_PALABRAS_CLAVE.match(texto)
            )
            if es_ingles:
                _agregar_clase(elem, "keywords")
                contenido.keywords = str(elem)
            else:
                _agregar_clase(elem, "palabras-clave")
                contenido.palabras_clave = str(elem)
            continue
        if "sumario" in clases_lower:
            bloque_resumen = None
            contenido.sumario = str(elem)
            continue

        # --- datos del autor con otro estilo (correo, segunda adscripción...) ---
        # Siguen al autor en el HTML: se quedan con él aunque la clase no sea adscripcion_mail.
        if zona_autor and autor_actual is not None and elem.name == "p" and len(texto) < 250:
            elem["class"] = ["adscripcion_mail"]
            autor_actual.adscripciones_html.append(str(elem))
            continue

        # --- Cómo citar (viene como párrafos AB/PP al final del cuerpo) ---
        texto_lower = texto.lower().rstrip(":")
        if texto_lower in _KW_COMO_CITAR:
            en_como_citar = True
            contenido.como_citar.append(f'<p class="como_citar">{_html.escape(texto)}</p>')
            continue
        if en_como_citar:
            if texto_lower in ("iij-unam", "iij unam", "iijunam"):
                contenido.como_citar.append(f'<p class="iijunam">{_html.escape(texto)}</p>')
            elif texto_lower == "apa":
                contenido.como_citar.append('<p class="APA">APA</p>')
            else:
                _agregar_clase(elem, "cita")
                contenido.como_citar.append(str(elem))
            continue

        # --- título sin estilo de título ---
        # En reseñas y otros casos InDesign exporta el título (p. ej. la referencia del
        # libro reseñado) como párrafo normal. Si aparece antes del primer autor y
        # antes de cualquier otro dato, es el título.
        if (
            elem.name == "p"
            and autor_actual is None
            and not contenido.fechas
            and not contenido.doi_html
            and not contenido.resumen
            and not contenido.cuerpo
            and len(texto) < 500
            and not elem.find("img")
            and not (contenido.titulo_es and contenido.titulo_en)
        ):
            es_principal = not contenido.titulo_es
            elem.name = "h1" if es_principal else "h2"
            elem["class"] = ["TCC-1" if es_principal else "TCC-2", "titulo_referencia"]
            _neutralizar_br(elem)
            if es_principal:
                contenido.titulo_es = str(elem)
            else:
                contenido.titulo_en = str(elem)
            continue

        # --- figuras ---
        if elem.find("img"):
            _agregar_clase(elem, "figura")
            contenido.cuerpo.append(str(elem))
            ultimo_fue_figura = True
            continue
        if _RE_TITULO_FIGURA.match(texto):
            _agregar_clase(elem, "titulo_figura")
        elif ultimo_fue_figura and _RE_FUENTE_FIGURA.match(texto):
            _agregar_clase(elem, "fuente_figura")
        ultimo_fue_figura = False

        # --- citas en bloque (trun, trp, tri, trpu...) ---
        if any(c in _ESTILOS_CITA_BLOQUE for c in clases_lower):
            _agregar_clase(elem, "cita_bloque")

        # --- cuerpo, encabezados y referencias (se conserva el orden original) ---
        contenido.cuerpo.append(str(elem))

    _reubicar_correos(contenido)
    contenido.cuerpo = _agrupar_epigrafe(contenido.cuerpo)
    return contenido


_RE_ENCABEZADO = re.compile(r"^<h[345][\s>]")
_RE_CORREO = re.compile(
    r"(correo(\s+electr[oó]nico)?|e-?mail)\s*:|[\w.+-]+@[\w-]+(\.[\w-]+)+",
    re.IGNORECASE,
)


def _es_correo(elem: Tag) -> bool:
    texto = _texto(elem)
    return len(texto) < 160 and bool(_RE_CORREO.search(texto))


def _reubicar_correos(contenido: "ContenidoArticulo") -> None:
    """
    Red de seguridad: un correo que haya quedado suelto antes del primer
    encabezado (por traer un estilo de párrafo distinto) se devuelve a su autor.
    Se asigna, en orden, al primer autor que aún no tiene correo.
    """
    if not contenido.autores_obj:
        return
    idx = next((i for i, b in enumerate(contenido.cuerpo) if _RE_ENCABEZADO.match(b)), len(contenido.cuerpo))

    restantes, correos = [], []
    for i, bloque in enumerate(contenido.cuerpo):
        p = BeautifulSoup(bloque, "html.parser").find("p") if i < idx and bloque.startswith("<p") else None
        if p is not None and _es_correo(p):
            p["class"] = ["adscripcion_mail"]
            correos.append(str(p))
        else:
            restantes.append(bloque)
    if not correos:
        return

    def tiene_correo(autor: Autor) -> bool:
        return any(_RE_CORREO.search(_texto(BeautifulSoup(a, "html.parser"))) for a in autor.adscripciones_html)

    for correo in correos:
        sin_correo = [a for a in contenido.autores_obj if not tiene_correo(a)]
        destino = sin_correo[0] if sin_correo else contenido.autores_obj[-1]
        destino.adscripciones_html.append(correo)
    contenido.cuerpo = restantes


def _agrupar_epigrafe(cuerpo: List[str]) -> List[str]:
    """
    Si antes del primer encabezado hay una cita corta (epígrafe + fuente), la
    agrupa en <div class="epigrafe"> para colocarla como bloque ordenado.
    Con textos largos o elementos que no son párrafos no hace nada.
    """
    idx = next((i for i, b in enumerate(cuerpo) if _RE_ENCABEZADO.match(b)), 0)
    if idx == 0:
        return cuerpo

    previos = cuerpo[:idx]
    sopas = [BeautifulSoup(b, "html.parser") for b in previos]
    parrafos = [s.find("p") for s in sopas]
    if any(p is None or p.find(["img", "table"]) for p in parrafos):
        return cuerpo
    if sum(len(_texto(p)) for p in parrafos) > 600:
        return cuerpo

    partes = []
    for i, p in enumerate(parrafos):
        es_fuente = len(parrafos) > 1 and i == len(parrafos) - 1
        p["class"] = ["epigrafe_fuente" if es_fuente else "epigrafe_texto"]
        partes.append(str(p))
    bloque = '<div class="epigrafe">\n\t' + "\n\t".join(partes) + "\n</div>"
    return [bloque, *cuerpo[idx:]]


def _cierra_bloque_resumen(hijos: List[Tag], i: int) -> bool:
    """
    ¿Más adelante (antes del Sumario o del primer encabezado) hay unas Palabras
    clave/Keywords que cierren el bloque de resumen? Sirve para saber si un párrafo
    sin estilo reconocido, entre el resumen y las palabras clave, es su continuación.
    """
    for sig in hijos[i + 1:]:
        if not isinstance(sig, Tag):
            continue
        clases = [c.lower() for c in (sig.get("class") or [])]
        if "palabras-clave" in clases or "keywords" in clases:
            return True
        if "sumario" in clases or sig.name in ("h3", "h4", "h5"):
            return False
    return False


def _html_interno(elem: Tag) -> str:
    return "".join(str(child) for child in elem.children)


# ----------------------------------------------------------------------
# Generación
# ----------------------------------------------------------------------
def generar_html_referencia(contenido: ContenidoArticulo, css_inline: str, nombre_revista: str) -> str:
    css_tags = f"<style>\n{css_inline}\n\t\t</style>"

    bloques_autores: List[str] = []
    for autor in contenido.autores_obj:
        partes = []
        if autor.nombre_html:
            partes.append(f'<p class="AUT">{autor.nombre_html}</p>')
        orcid = _html_orcid(autor)
        if orcid:
            partes.append(orcid)
        partes.extend(autor.adscripciones_html)
        bloques_autores.append('<div class="autor">\n\t' + "\n\t".join(partes) + "\n</div>")

    bloque_fechas = ""
    if contenido.fechas:
        bloque_fechas = '<div class="fechas">\n\t' + "\n\t".join(contenido.fechas) + "\n</div>"

    bloque_como_citar = ""
    if contenido.como_citar:
        bloque_como_citar = (
            '<div class="como_citar_section">\n\t' + "\n\t".join(contenido.como_citar) + "\n</div>"
        )

    tipo = (
        f'<p class="tipo_articulo">{_html.escape(contenido.tipo_articulo)}</p>'
        if contenido.tipo_articulo
        else ""
    )

    encabezado = [
        tipo,
        contenido.titulo_es,
        contenido.titulo_en,
        *bloques_autores,
        bloque_fechas,
        contenido.doi_html,
        *(
            [contenido.abstract, contenido.keywords, contenido.resumen, contenido.palabras_clave]
            if contenido.abstract_primero
            else [contenido.resumen, contenido.palabras_clave, contenido.abstract, contenido.keywords]
        ),
        contenido.sumario,
    ]
    cuerpo = [*contenido.cuerpo, bloque_como_citar, contenido.notas_html]

    interior = _indentar_html([b for b in [*encabezado, *cuerpo] if b], 4)

    html = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="es-ES">
\t<head>
\t\t<meta charset="utf-8" />
\t\t<meta name="viewport" content="width=device-width, initial-scale=1.0" />
\t\t<title>{_html.escape(nombre_revista)}</title>
\t\t{css_tags}
\t</head>
\t<body id="x{nombre_revista}">
\t\t<div class="contenedor">
\t\t\t<div id="_idContainer002" class="_idGenObjectStyleOverride-1">
\t\t\t\t{interior}
\t\t\t</div>
\t\t</div>
\t</body>
</html>"""

    return re.sub(r"\n\s*\n", "\n", html)


def _corregir_rutas_imagenes(html: str) -> str:
    def reemplazar_y_sanitizar(match):
        nombre = unicodedata.normalize("NFKD", urllib.parse.unquote(match.group(1))).encode("ASCII", "ignore").decode("utf-8")
        return f'src="{re.sub(r"[^\w\.-]", "_", nombre)}"'

    return re.sub(r'src="[^"]*?(?:web-resources/image/|image/)([^"]+)"', reemplazar_y_sanitizar, html)


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
            contenido.tipo_articulo = tipo_articulo_forzado

        html_final = generar_html_referencia(contenido, css_inline, nombre_revista)
        html_final = _corregir_rutas_imagenes(html_final)
        # Enlaces internos (notas al pie): "archivo.html#ancla" -> "#ancla"
        html_final = re.sub(r'href="[^"#]*\.html(#[^"]+)"', r'href="\1"', html_final)

        with open(ruta_salida_html, "w", encoding="utf-8") as f:
            f.write(html_final)
        return True
    except Exception as e:
        print(f"    ✗ Error procesando HTML Problema: {e}")
        return False