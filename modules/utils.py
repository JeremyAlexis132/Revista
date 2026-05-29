"""
Módulo de utilidades para el procesador de revistas.

Incluye funciones para:
- Lectura/escritura de la bitácora (bitacora.json)
- Creación de estructura de carpetas de salida
- Copia de imágenes con corrección de rutas y sanitización de nombres
"""

import json
import os
import shutil
import re
import urllib.parse
import unicodedata
from pathlib import Path
from typing import List, Optional


# ──────────────────────────────────────────────────────────
#  Bitácora
# ──────────────────────────────────────────────────────────

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
        json.dump(ids_existentes, f, ensure_ascii=False, indent=2)


# ──────────────────────────────────────────────────────────
#  Estructura de carpetas
# ──────────────────────────────────────────────────────────

def crear_estructura_salida(carpeta_salida: str, nombre_revista: str) -> dict:
    base = os.path.join(carpeta_salida, nombre_revista)
    css_dir = os.path.join(base, "css")
    images_dir = os.path.join(base, "images")

    os.makedirs(css_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)

    return {
        "base": base,
        "css": css_dir,
        "images": images_dir,
        "html": os.path.join(base, "index.html"),
    }


# ──────────────────────────────────────────────────────────
#  Imágenes y Sanitización
# ──────────────────────────────────────────────────────────

def sanitizar_nombre_archivo(nombre: str) -> str:
    """
    Limpia el nombre del archivo: decodifica URLs, quita acentos, 
    y reemplaza espacios o caracteres raros por guiones bajos.
    """
    # 1. Decodificar caracteres URL (ej. %C3%A1 -> á)
    nombre = urllib.parse.unquote(nombre)
    # 2. Quitar acentos separando el caracter base de su tilde
    nombre = unicodedata.normalize('NFKD', nombre).encode('ASCII', 'ignore').decode('utf-8')
    # 3. Reemplazar todo lo que no sea alfanumérico, punto o guion por un guion bajo
    nombre = re.sub(r'[^\w\.-]', '_', nombre)
    return nombre


def copiar_imagenes(carpeta_origen: str, carpeta_destino: str) -> List[str]:
    extensiones_img = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp", ".tiff"}
    copiados: List[str] = []

    for root, _dirs, files in os.walk(carpeta_origen):
        for archivo in files:
            if Path(archivo).suffix.lower() in extensiones_img:
                origen = os.path.join(root, archivo)
                
                # Generamos un nombre seguro para web y editores locales
                nombre_seguro = sanitizar_nombre_archivo(archivo)
                destino = os.path.join(carpeta_destino, nombre_seguro)
                
                # Evitar sobrescribir si ya existe un archivo con el mismo nombre
                if os.path.exists(destino):
                    base, ext = os.path.splitext(nombre_seguro)
                    contador = 1
                    while os.path.exists(destino):
                        destino = os.path.join(carpeta_destino, f"{base}_{contador}{ext}")
                        contador += 1
                        
                shutil.copy2(origen, destino)
                copiados.append(os.path.basename(destino))

    return copiados

# ──────────────────────────────────────────────────────────
#  Identificadores de sección
# ──────────────────────────────────────────────────────────

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
    css_files: List[str] = []
    for root, _dirs, files in os.walk(carpeta):
        for archivo in files:
            if archivo.lower().endswith(".css"):
                css_files.append(os.path.join(root, archivo))
    return css_files