"""Adaptador HTML de RMDH al extractor y formato visual de CC."""

import os
import re
import tempfile
from typing import Optional

from bs4 import BeautifulSoup

from Modules.journals.cc import html_processor as cc


def _normalizar_html_rmdh(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    equivalencias = {
        "TCC_esp": "titulo_espanol",
        "TCC_ing": "titulo_ingles",
        "TCC-1": "titulo_espanol",
        "TCC-2": "titulo_ingles",
        "VV": "romanos",
        "IA": "arabigos",
        "AUT1": "aut",
        "AUT2": "aut",
        "nota-de-autor": "nota-de-autor-final",
        "e-mail": "correo",
        "PP": "cuerpo_texto",
        "BODY-text": "cuerpo_texto",
    }
    for tag in soup.find_all(True):
        clases = tag.get("class", [])
        nuevas_clases = [equivalencias.get(clase, clase) for clase in clases]
        nuevas_clases = [
            clase for clase in nuevas_clases
            if "texto-nota-pie" not in clase.lower() and "nota-pie" not in clase.lower()
        ]
        tag["class"] = nuevas_clases
        if not nuevas_clases:
            tag.attrs.pop("class", None)
        if "titulo_espanol" in nuevas_clases:
            tag.name = "h1"
        elif "titulo_ingles" in nuevas_clases:
            tag.name = "h2"
    return str(soup)


def _texto_como_citar(contenido: cc.ContenidoArticulo) -> str:
    return " ".join(BeautifulSoup(bloque, "html.parser").get_text(" ") for bloque in contenido.como_citar)


def _identificadores_rmdh(contenido: cc.ContenidoArticulo) -> str:
    texto = _texto_como_citar(contenido)
    volumen = re.search(r"vol\.??\s*(\d+)", texto, re.IGNORECASE)
    numero = re.search(r"n[uú]m\.??\s*(\d+)", texto, re.IGNORECASE)
    ano = re.search(r"\b(20\d{2})\b", texto)
    articulo = re.search(r"\b(e\d{4,6})\b", texto, re.IGNORECASE)
    doi = contenido.doi_extraido or cc._extraer_url_doi(texto)
    volumen_numero = f"{volumen.group(1) if volumen else '[Vol]'}({numero.group(1) if numero else '[Núm]'})"
    ano_texto = ano.group(1) if ano else "[Año]"
    if articulo:
        e_id = articulo.group(1)
    else:
        identificador = contenido.identificadores[0] if contenido.identificadores else "[ID]"
        e_id = f"e{identificador}"
    doi_html = f'<a href="{doi}"><span class="hipervinculo">{doi}</span></a>' if doi else '<span class="hipervinculo">[colocar doi aquí]</span>'
    lineas = [
        f"Revista Mexicana de Historia del Derecho, {volumen_numero}, {ano_texto}, {e_id}",
        f"e-ISSN: 2448-7880  DOI: {doi_html}",
        'Esta obra está bajo una <a href="https://creativecommons.org/licenses/by-nc/4.0/"><span class="hipervinculo">Licencia Creative Commons Reconocimiento-NoComercial 4.0 Internacional</span></a>',
        "Instituto de Investigaciones Jurídicas de la Universidad Nacional Autónoma de México",
    ]
    return "".join(f"<br>{linea}" for linea in lineas) + "<br><br>"


def _reemplazar_identificadores(html: str, contenido: cc.ContenidoArticulo) -> str:
    bloque = f'<p class="notas_iniciales">\n\t\t\t{_identificadores_rmdh(contenido)}\n\t\t</p>'
    return re.sub(r'<p class="notas_iniciales">.*?</p>', bloque, html, count=1, flags=re.DOTALL)


def procesar_html(
    html_path: str,
    css_inline: str,
    ruta_salida_html: str,
    nombre_revista: str,
    tipo_articulo_forzado: Optional[str] = None,
) -> bool:
    try:
        with open(html_path, "r", encoding="utf-8") as archivo:
            html_normalizado = _normalizar_html_rmdh(archivo.read())
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", encoding="utf-8", delete=False) as temporal:
            temporal.write(html_normalizado)
            temporal_path = temporal.name
        try:
            contenido = cc.extraer_contenido(temporal_path)
        finally:
            os.unlink(temporal_path)
        if tipo_articulo_forzado:
            contenido.tipo_articulo = tipo_articulo_forzado
        html_final = cc.generar_html_referencia(contenido, css_inline, nombre_revista)
        html_final = _reemplazar_identificadores(html_final, contenido)
        html_final = cc._corregir_rutas_imagenes(html_final)
        html_final = re.sub(r'href="[^"#]*\.html(#[^"]+)"', r'href="\1"', html_final)
        with open(ruta_salida_html, "w", encoding="utf-8") as archivo:
            archivo.write(html_final)
        return True
    except Exception as error:
        print(f"    ✗ Error procesando HTML RMDH: {error}")
        return False