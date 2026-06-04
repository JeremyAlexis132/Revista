"""
Módulo de utilidades para el procesador de revistas.
"""

import json
import os
import shutil
import re
import urllib.parse
import unicodedata
from typing import List, Optional, Dict

def leer_bitacora(ruta_bitacora: str) -> List[str]:
    if not os.path.exists(ruta_bitacora):
        return []
    try:
        with open(ruta_bitacora, "r", encoding="utf-8") as f:
            datos = json.load(f)
        if isinstance(datos, list):
            return [str(d) for d in datos]
        return []
    except (json.JSONDecodeError, IOError):
        return []

def registrar_en_bitacora(ruta_bitacora: str, revista_id: str) -> None:
    ids_existentes = leer_bitacora(ruta_bitacora)
    if revista_id not in ids_existentes:
        ids_existentes.append(revista_id)
    with open(ruta_bitacora, "w", encoding="utf-8") as f:
        json.dump(ids_existentes, f, indent=4)

def extraer_id_de_carpeta(nombre_carpeta: str) -> Optional[str]:
    match = re.match(r"^(\d+)", nombre_carpeta)
    return match.group(1) if match else None

def extraer_codigo_seccion(nombre_carpeta: str) -> str:
    patron = r"^\d+_rmde(?:_([a-z]{2}))?(?:-web-resources)?$"
    match = re.match(patron, nombre_carpeta.strip(), flags=re.IGNORECASE)
    if not match:
        return "art"

    codigo = match.group(1)
    if not codigo:
        return "art"

    codigo = codigo.lower()
    if codigo in {"nm", "ej", "ar", "oe"}:
        return codigo
    return "art"

def construir_clave_bitacora(nombre_carpeta: str) -> Optional[str]:
    revista_id = extraer_id_de_carpeta(nombre_carpeta)
    if revista_id is None:
        return None
    codigo = extraer_codigo_seccion(nombre_carpeta)
    return f"{revista_id}:{codigo}"

def encontrar_html_en_carpeta(carpeta: str) -> Optional[str]:
    for item in os.listdir(carpeta):
        if item.lower().endswith(".html") and not item.startswith("."):
            return os.path.join(carpeta, item)
    return None

def encontrar_css_en_carpeta(carpeta: str) -> List[str]:
    css_paths = []
    for root, dirs, files in os.walk(carpeta):
        for file in files:
            if file.lower().endswith(".css") and not file.startswith("."):
                css_paths.append(os.path.join(root, file))
    return css_paths

def crear_estructura_salida(directorio_base: str, nombre_carpeta: str) -> Dict[str, str]:
    ruta_carpeta = os.path.join(directorio_base, nombre_carpeta)
    if not os.path.exists(ruta_carpeta):
        os.makedirs(ruta_carpeta)

    # Ahora TODO apunta a la misma ruta principal (sin subcarpetas css o images)
    return {
        "base": ruta_carpeta,
        "html": os.path.join(ruta_carpeta, "index.html"),
        "images": ruta_carpeta,
        "css": ruta_carpeta
    }

def copiar_imagenes(ruta_origen: str, ruta_destino: str) -> None:
    carpetas_img = []
    for root, dirs, files in os.walk(ruta_origen):
        if os.path.basename(root).lower() == "image":
            carpetas_img.append(root)

    for carpeta in carpetas_img:
        for item in os.listdir(carpeta):
            if item.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp')):
                src = os.path.join(carpeta, item)
                nombre = urllib.parse.unquote(item)
                nombre = unicodedata.normalize('NFKD', nombre).encode('ASCII', 'ignore').decode('utf-8')
                nombre = re.sub(r'[^\w\.-]', '_', nombre)
                dst = os.path.join(ruta_destino, nombre)
                shutil.copy2(src, dst)