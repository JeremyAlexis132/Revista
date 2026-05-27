#!/usr/bin/env python3
"""
Gestor principal del Procesador de Revistas Académicas RMDE.

Escanea carpetas en Archivos/, extrae contenido de cada revista,
reestructura el HTML al formato de referencia de la RMDE, y genera
la salida en Salida/.

Uso:
    python main.py

Estructura esperada de Archivos/:
    Archivos/
    └── 20462_rmde/
        ├── css/                         (opcional)
        ├── image/                       (opcional)
        ├── 20462_rmde-web-resources/    (carpeta de recursos de InDesign)
        │   ├── css/
        │   └── image/
        ├── 20462_rmde.html
        └── .DS_Store                    (ignorado)

Salida generada en Salida/:
    Salida/
    └── 20462_rmde/
        ├── index.html
        ├── css/
        │   ├── idGeneratedStyles.css    (CSS corregido)
        │   └── referencia.css           (CSS de referencia adicional)
        └── images/
            └── *.png, *.jpg, ...
"""

import os
import sys
import time

# Agregar el directorio del proyecto al path
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

from Modules.utils import (
    leer_bitacora,
    registrar_en_bitacora,
    crear_estructura_salida,
    copiar_imagenes,
    extraer_id_de_carpeta,
    encontrar_html_en_carpeta,
    encontrar_css_en_carpeta,
)
from Modules.html_processor import procesar_html
from Modules.css_processor import procesar_css


# ──────────────────────────────────────────────────────────
#  Configuración
# ──────────────────────────────────────────────────────────

ARCHIVOS_DIR = os.path.join(PROJECT_DIR, "Archivos")
SALIDA_DIR = os.path.join(PROJECT_DIR, "Salida")
BITACORA_PATH = os.path.join(PROJECT_DIR, "bitacora.json")


# ──────────────────────────────────────────────────────────
#  Funciones auxiliares
# ──────────────────────────────────────────────────────────

def imprimir_banner() -> None:
    """Muestra el banner del proyecto en consola."""
    print("=" * 60)
    print("  📚 Procesador de Revistas Académicas RMDE")
    print("  Formato de referencia: revistas.juridicas.unam.mx")
    print("=" * 60)
    print()


def escanear_carpetas() -> list:
    """Escanea la carpeta Archivos/ y devuelve las subcarpetas válidas.

    Returns:
        Lista de tuplas (nombre_carpeta, ruta_completa).
    """
    if not os.path.exists(ARCHIVOS_DIR):
        os.makedirs(ARCHIVOS_DIR, exist_ok=True)
        print(f"  📁 Carpeta Archivos/ creada en: {ARCHIVOS_DIR}")
        return []

    carpetas = []
    for item in sorted(os.listdir(ARCHIVOS_DIR)):
        ruta = os.path.join(ARCHIVOS_DIR, item)
        if os.path.isdir(ruta) and not item.startswith("."):
            carpetas.append((item, ruta))

    return carpetas


def procesar_revista(nombre: str, ruta: str) -> bool:
    """Procesa una revista individual.

    Args:
        nombre: Nombre de la carpeta de la revista.
        ruta: Ruta completa a la carpeta.

    Returns:
        True si se procesó correctamente, False en caso contrario.
    """
    print(f"\n  📖 Procesando: {nombre}")
    print(f"  {'─' * 50}")

    # 1. Encontrar archivo HTML
    html_path = encontrar_html_en_carpeta(ruta)
    if html_path is None:
        print(f"    ✗ No se encontró archivo HTML en {nombre}")
        return False
    print(f"    ✓ HTML encontrado: {os.path.basename(html_path)}")

    # 2. Encontrar archivos CSS
    css_paths = encontrar_css_en_carpeta(ruta)
    if css_paths:
        print(f"    ✓ CSS encontrados: {len(css_paths)} archivo(s)")
    else:
        print(f"    ⚠ No se encontraron archivos CSS")

    # 3. Crear estructura de salida
    rutas = crear_estructura_salida(SALIDA_DIR, nombre)
    print(f"    ✓ Estructura de salida creada")

    # 4. Copiar y corregir CSS
    archivos_css = procesar_css(css_paths, rutas["css"], nombre)

    # 5. Copiar imágenes
    imagenes = copiar_imagenes(ruta, rutas["images"])
    if imagenes:
        print(f"    ✓ Imágenes copiadas: {len(imagenes)} archivo(s)")
    else:
        print(f"    ⚠ No se encontraron imágenes")

    # 6. Procesar HTML
    exito = procesar_html(
        html_path=html_path,
        archivos_css=archivos_css,
        ruta_salida_html=rutas["html"],
        nombre_revista=nombre,
    )

    return exito


# ──────────────────────────────────────────────────────────
#  Punto de entrada
# ──────────────────────────────────────────────────────────

def main() -> None:
    """Función principal del procesador."""
    inicio = time.time()
    imprimir_banner()

    # Escanear carpetas en Archivos/
    carpetas = escanear_carpetas()
    if not carpetas:
        print("  ⚠ No se encontraron carpetas de revistas en Archivos/")
        print(f"    Coloque las carpetas en: {ARCHIVOS_DIR}")
        return

    print(f"  📂 Carpetas encontradas: {len(carpetas)}")

    # Leer bitácora
    ids_procesados = leer_bitacora(BITACORA_PATH)
    if ids_procesados:
        print(f"  📋 IDs ya procesados: {', '.join(ids_procesados)}")
    else:
        print(f"  📋 Bitácora vacía — no hay IDs procesados anteriormente")

    # Contadores
    procesadas = 0
    omitidas = 0
    errores = 0

    for nombre, ruta in carpetas:
        revista_id = extraer_id_de_carpeta(nombre)

        if revista_id is None:
            print(f"\n  ⚠ No se pudo extraer ID de: {nombre} — Omitiendo")
            errores += 1
            continue

        # Verificar si ya fue procesado
        if revista_id in ids_procesados:
            print(f"\n  ⏭  {nombre} (ID: {revista_id}) — Ya procesado, omitiendo")
            omitidas += 1
            continue

        # Procesar
        exito = procesar_revista(nombre, ruta)

        if exito:
            registrar_en_bitacora(BITACORA_PATH, revista_id)
            procesadas += 1
            print(f"  ✅ {nombre} procesada exitosamente")
        else:
            errores += 1
            print(f"  ❌ Error al procesar {nombre}")

    # Resumen final
    duracion = time.time() - inicio
    print(f"\n{'=' * 60}")
    print(f"  📊 Resumen:")
    print(f"     Procesadas:  {procesadas}")
    print(f"     Omitidas:    {omitidas}")
    print(f"     Errores:     {errores}")
    print(f"     Tiempo:      {duracion:.2f} segundos")
    print(f"     Salida en:   {SALIDA_DIR}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
