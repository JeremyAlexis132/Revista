#!/usr/bin/env python3
"""
Gestor principal del procesador de revistas RMDE.
"""

import os
import sys
import time

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

from Modules.journals.rmde.css_processor import procesar_y_combinar_css
from Modules.core.sections import obtener_procesador_por_seccion
from Modules.journals.rmde.utils import (
    construir_clave_bitacora,
    crear_estructura_salida,
    copiar_imagenes,
    encontrar_css_en_carpeta,
    encontrar_html_en_carpeta,
    extraer_codigo_seccion,
    extraer_id_de_carpeta,
    leer_bitacora,
    registrar_en_bitacora,
)

def resolver_archivos_dir() -> str:
    candidatos = ["Archivos", "archivos"]
    for nombre in candidatos:
        ruta = os.path.join(PROJECT_DIR, nombre)
        if os.path.exists(ruta):
            return ruta
    return os.path.join(PROJECT_DIR, "archivos")

ARCHIVOS_DIR = resolver_archivos_dir()
SALIDA_DIR = os.path.join(PROJECT_DIR, "Salida")
BITACORA_PATH = os.path.join(PROJECT_DIR, "bitacora.json")

def imprimir_banner() -> None:
    print("=" * 60)
    print("  PROCESADOR DE REVISTAS RMDE")
    print("=" * 60)

def procesar_revista(nombre_carpeta: str, ruta_carpeta: str) -> bool:
    html_path = encontrar_html_en_carpeta(ruta_carpeta)
    if html_path is None:
        print(f"  Error: No se encontro archivo HTML en {nombre_carpeta}")
        return False

    css_paths = encontrar_css_en_carpeta(ruta_carpeta)
    rutas = crear_estructura_salida(SALIDA_DIR, nombre_carpeta)

    # 1. Obtener CSS unificado
    css_inline = procesar_y_combinar_css(css_paths)
    
    # 2. Copiar imagenes a la base
    copiar_imagenes(ruta_carpeta, rutas["images"])

    codigo_seccion = extraer_codigo_seccion(nombre_carpeta)
    procesador_html = obtener_procesador_por_seccion(codigo_seccion)

    # 3. Procesar HTML
    return procesador_html(
        html_path=html_path,
        css_inline=css_inline,
        ruta_salida_html=rutas["html"],
        nombre_revista=nombre_carpeta,
    )

def main() -> None:
    imprimir_banner()

    if not os.path.exists(ARCHIVOS_DIR):
        print(f"\n  Error: No existe la carpeta de entrada '{ARCHIVOS_DIR}'")
        return

    carpetas = []
    for item in os.listdir(ARCHIVOS_DIR):
        ruta = os.path.join(ARCHIVOS_DIR, item)
        if os.path.isdir(ruta) and not item.startswith("."):
            carpetas.append((item, ruta))

    if not carpetas:
        print(f"\n  No hay carpetas para procesar en '{ARCHIVOS_DIR}'")
        return

    ids_procesados = leer_bitacora(BITACORA_PATH)
    inicio = time.time()
    procesadas = 0
    omitidas = 0
    errores = 0

    for nombre, ruta in carpetas:
        revista_id = extraer_id_de_carpeta(nombre)
        clave_bitacora = construir_clave_bitacora(nombre)

        if revista_id is None or clave_bitacora is None:
            print(f"\n  Aviso: no se pudo extraer ID de {nombre}, se omite")
            errores += 1
            continue

        procesada_en_bitacora_nueva = clave_bitacora in ids_procesados
        procesada_en_bitacora_legacy = (
            revista_id in ids_procesados and clave_bitacora.endswith(":art")
        )

        if procesada_en_bitacora_nueva or procesada_en_bitacora_legacy:
            print(f"\n  Saltando {nombre} (ID: {revista_id}) - ya procesado")
            omitidas += 1
            continue

        exito = procesar_revista(nombre, ruta)

        if exito:
            registrar_en_bitacora(BITACORA_PATH, clave_bitacora)
            ids_procesados.append(clave_bitacora)
            procesadas += 1
            print(f"  OK {nombre} procesada")
        else:
            errores += 1
            print(f"  Error al procesar {nombre}")

    duracion = time.time() - inicio
    print(f"\n{'=' * 60}")
    print("  Resumen:")
    print(f"     Procesadas: {procesadas}")
    print(f"     Omitidas:   {omitidas}")
    print(f"     Errores:    {errores}")
    print(f"     Tiempo:     {duracion:.2f} s")
    print("=" * 60)

if __name__ == "__main__":
    main()