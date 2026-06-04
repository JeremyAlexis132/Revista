#!/usr/bin/env python3
"""
Gestor principal del procesador de revistas académicas.
"""

import os
import sys
import time

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

from Modules.core.sections import obtener_procesador_por_seccion
from Modules.core.utils_base import (
    crear_estructura_salida,
    copiar_imagenes,
    encontrar_css_en_carpeta,
    encontrar_html_en_carpeta,
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
    print("  PROCESADOR DE REVISTAS ACADÉMICAS")
    print("=" * 60)

def seleccionar_revista() -> str:
    while True:
        print("\nSeleccione la revista a procesar:")
        print("  1. Revista Mexicana de Derecho Electoral (RMDE)")
        print("  2. Cuestiones Constitucionales (CC)")
        print("  3. Salir")
        opcion = input("\nIngrese el número de la opción: ").strip()

        if opcion == "1":
            return "rmde"
        elif opcion == "2":
            return "cc"
        elif opcion == "3":
            print("\n  Saliendo del programa...")
            sys.exit(0)
        else:
            print("\n  [Error] Opción no válida. Por favor, intente de nuevo.")

def procesar_carpeta_revista(
    nombre_carpeta: str, 
    ruta_carpeta: str, 
    procesador_css, 
    procesador_html
) -> bool:
    """Flujo genérico de procesamiento aplicado a cualquier revista."""
    html_path = encontrar_html_en_carpeta(ruta_carpeta)
    if html_path is None:
        print(f"  Error: No se encontró archivo HTML en {nombre_carpeta}")
        return False

    css_paths = encontrar_css_en_carpeta(ruta_carpeta)
    rutas = crear_estructura_salida(SALIDA_DIR, nombre_carpeta)

    # 1. Obtener CSS unificado
    css_inline = procesador_css(css_paths)
    
    # 2. Copiar imágenes a la base
    copiar_imagenes(ruta_carpeta, rutas["images"])

    # 3. Procesar HTML
    return procesador_html(
        html_path=html_path,
        css_inline=css_inline,
        ruta_salida_html=rutas["html"],
        nombre_revista=nombre_carpeta,
    )

def main() -> None:
    imprimir_banner()

    revista_seleccionada = seleccionar_revista()

    # Importaciones dinámicas según la revista seleccionada
    if revista_seleccionada == "rmde":
        from Modules.journals.rmde.utils import extraer_id_de_carpeta, extraer_codigo_seccion, construir_clave_bitacora, es_carpeta_valida
        from Modules.journals.rmde.css_processor import procesar_y_combinar_css
        print(f"\nIniciando procesamiento para RMDE...")
        
    elif revista_seleccionada == "cc":
        from Modules.journals.cc.utils import extraer_id_de_carpeta, extraer_codigo_seccion, construir_clave_bitacora, es_carpeta_valida
        from Modules.journals.cc.css_processor import procesar_y_combinar_css
        print(f"\nIniciando procesamiento para Cuestiones Constitucionales (CC)...")

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
        # 1. Ignorar las carpetas que no corresponden a la revista seleccionada
        if not es_carpeta_valida(nombre):
            continue

        revista_id = extraer_id_de_carpeta(nombre)
        clave_bitacora = construir_clave_bitacora(nombre)

        if revista_id is None or clave_bitacora is None:
            print(f"\n  Aviso: no se pudo extraer ID de {nombre}, se omite.")
            errores += 1
            continue

        procesada_en_bitacora_nueva = clave_bitacora in ids_procesados
        procesada_en_bitacora_legacy = (
            revista_id in ids_procesados and clave_bitacora.endswith(":art")
        )

        if procesada_en_bitacora_nueva or procesada_en_bitacora_legacy:
            print(f"\n  Saltando {nombre} (ID: {revista_id}) - ya procesado.")
            omitidas += 1
            continue

        # 2. Configurar el procesador HTML con la fábrica de secciones
        codigo_seccion = extraer_codigo_seccion(nombre)
        procesador_html_configurado = obtener_procesador_por_seccion(revista_seleccionada, codigo_seccion)

        # 3. Ejecutar procesamiento
        exito = procesar_carpeta_revista(
            nombre_carpeta=nombre, 
            ruta_carpeta=ruta, 
            procesador_css=procesar_y_combinar_css, 
            procesador_html=procesador_html_configurado
        )

        if exito:
            registrar_en_bitacora(BITACORA_PATH, clave_bitacora)
            ids_procesados.append(clave_bitacora)
            procesadas += 1
            print(f"  OK {nombre} procesada.")
        else:
            errores += 1
            print(f"  Error al procesar {nombre}.")

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