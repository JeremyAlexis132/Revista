"""
Módulo de utilidades para el procesador de revistas.

Incluye funciones para:
- Lectura/escritura de la bitácora (bitacora.json)
- Creación de estructura de carpetas de salida
- Copia de imágenes con corrección de rutas
"""

import json
import os
import shutil
import re
from pathlib import Path
from typing import List, Optional


# ──────────────────────────────────────────────────────────
#  Bitácora
# ──────────────────────────────────────────────────────────

def leer_bitacora(ruta_bitacora: str) -> List[str]:
    """Lee la bitácora JSON y devuelve la lista de IDs ya procesados.

    Args:
        ruta_bitacora: Ruta absoluta o relativa al archivo bitacora.json.

    Returns:
        Lista de cadenas con los IDs previamente procesados.
    """
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
    """Agrega un ID a la bitácora sin borrar los registros anteriores.

    Args:
        ruta_bitacora: Ruta al archivo bitacora.json.
        revista_id: ID de la revista procesada (ej. "20462").
    """
    ids_existentes = leer_bitacora(ruta_bitacora)
    if revista_id not in ids_existentes:
        ids_existentes.append(revista_id)
    with open(ruta_bitacora, "w", encoding="utf-8") as f:
        json.dump(ids_existentes, f, ensure_ascii=False, indent=2)


# ──────────────────────────────────────────────────────────
#  Estructura de carpetas
# ──────────────────────────────────────────────────────────

def crear_estructura_salida(carpeta_salida: str, nombre_revista: str) -> dict:
    """Crea la estructura de carpetas de salida para una revista.

    Estructura generada:
        Salida/<nombre_revista>/
            ├── index.html
            ├── css/
            └── images/

    Args:
        carpeta_salida: Ruta a la carpeta 'Salida'.
        nombre_revista: Nombre de la carpeta de la revista (ej. "20462_rmde").

    Returns:
        Diccionario con las rutas creadas:
            - 'base': ruta base de la revista
            - 'css': ruta a la carpeta css/
            - 'images': ruta a la carpeta images/
            - 'html': ruta al archivo index.html
    """
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
#  Imágenes
# ──────────────────────────────────────────────────────────

def copiar_imagenes(carpeta_origen: str, carpeta_destino: str) -> List[str]:
    """Copia todas las imágenes encontradas en la carpeta de origen al destino.

    Busca imágenes en:
      - <carpeta_origen>/image/
      - <carpeta_origen>/<nombre>-web-resources/image/
      - Cualquier subcarpeta que contenga archivos de imagen

    Args:
        carpeta_origen: Carpeta raíz de la revista de entrada.
        carpeta_destino: Carpeta images/ de salida.

    Returns:
        Lista de nombres de archivos copiados.
    """
    extensiones_img = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp", ".tiff"}
    copiados: List[str] = []

    for root, _dirs, files in os.walk(carpeta_origen):
        for archivo in files:
            if Path(archivo).suffix.lower() in extensiones_img:
                origen = os.path.join(root, archivo)
                destino = os.path.join(carpeta_destino, archivo)
                # Evitar sobrescribir si ya existe con el mismo nombre
                if os.path.exists(destino):
                    base, ext = os.path.splitext(archivo)
                    contador = 1
                    while os.path.exists(destino):
                        destino = os.path.join(carpeta_destino, f"{base}_{contador}{ext}")
                        contador += 1
                shutil.copy2(origen, destino)
                copiados.append(os.path.basename(destino))

    return copiados


def extraer_id_de_carpeta(nombre_carpeta: str) -> Optional[str]:
    """Extrae el ID numérico del nombre de una carpeta de revista.

    Ejemplos:
        "20462_rmde" → "20462"
        "12345_rmde" → "12345"

    Args:
        nombre_carpeta: Nombre de la carpeta.

    Returns:
        El ID como cadena, o None si no se pudo extraer.
    """
    match = re.match(r"^(\d+)", nombre_carpeta)
    return match.group(1) if match else None


def encontrar_html_en_carpeta(carpeta: str) -> Optional[str]:
    """Encuentra el archivo HTML principal dentro de una carpeta de revista.

    Ignora archivos .DS_Store y busca archivos con extensión .html.

    Args:
        carpeta: Ruta a la carpeta de la revista.

    Returns:
        Ruta absoluta al archivo HTML encontrado, o None.
    """
    for item in os.listdir(carpeta):
        if item.lower().endswith(".html") and not item.startswith("."):
            return os.path.join(carpeta, item)
    return None


def encontrar_css_en_carpeta(carpeta: str) -> List[str]:
    """Encuentra todos los archivos CSS en una carpeta de revista.

    Busca en:
      - <carpeta>/css/
      - <carpeta>/<nombre>-web-resources/css/
      - Subcarpetas con archivos .css

    Args:
        carpeta: Ruta a la carpeta de la revista.

    Returns:
        Lista de rutas absolutas a archivos CSS.
    """
    css_files: List[str] = []
    for root, _dirs, files in os.walk(carpeta):
        for archivo in files:
            if archivo.lower().endswith(".css"):
                css_files.append(os.path.join(root, archivo))
    return css_files
