#!/usr/bin/env python3
"""
Gestor principal del procesador de revistas académicas.
Procesa automáticamente todas las carpetas detectando a qué revista pertenecen.
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

# Importaciones de RMDE
from Modules.journals.rmde.utils import (
    extraer_id_de_carpeta as ext_id_rmde, 
    extraer_codigo_seccion as ext_sec_rmde, 
    construir_clave_bitacora as bitacora_rmde, 
    es_carpeta_valida as valida_rmde
)
from Modules.journals.rmde.css_processor import procesar_y_combinar_css as css_rmde

# Importaciones de CC
from Modules.journals.cc.utils import (
    extraer_id_de_carpeta as ext_id_cc, 
    extraer_codigo_seccion as ext_sec_cc, 
    construir_clave_bitacora as bitacora_cc, 
    es_carpeta_valida as valida_cc
)
from Modules.journals.cc.css_processor import procesar_y_combinar_css as css_cc


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
    print("  PROCESADOR AUTOMÁTICO DE REVISTAS ACADÉMICAS")
    print("=" * 60)

def procesar_carpeta_revista(
    nombre_carpeta: str, 
    ruta_carpeta: str, 
    procesador_css, 
    procesador_html,
    salida_base: str
) -> bool:
    """Flujo genérico de procesamiento aplicado a cualquier revista."""
    html_path = encontrar_html_en_carpeta(ruta_carpeta)
    if html_path is None:
        print(f"  Error: No se encontró archivo HTML en {nombre_carpeta}")
        return False

    css_paths = encontrar_css_en_carpeta(ruta_carpeta)
    
    # Crear la estructura dinámica en Salida/RMDE o Salida/CC
    rutas = crear_estructura_salida(salida_base, nombre_carpeta)

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
    print(f"\nIniciando procesamiento por lotes...\n")

    if not os.path.exists(ARCHIVOS_DIR):
        print(f"  Error: No existe la carpeta de entrada '{ARCHIVOS_DIR}'")
        return

    carpetas = []
    for item in os.listdir(ARCHIVOS_DIR):
        ruta = os.path.join(ARCHIVOS_DIR, item)
        if os.path.isdir(ruta) and not item.startswith("."):
            carpetas.append((item, ruta))

    if not carpetas:
        print(f"  No hay carpetas para procesar en '{ARCHIVOS_DIR}'")
        return

    ids_procesados = leer_bitacora(BITACORA_PATH)
    inicio = time.time()
    procesadas = 0
    omitidas = 0
    errores = 0

    for nombre, ruta in carpetas:
        # Detectar la revista dinámicamente
        if valida_rmde(nombre):
            revista = "rmde"
            ext_id = ext_id_rmde
            ext_sec = ext_sec_rmde
            const_bit = bitacora_rmde
            proc_css = css_rmde
        elif valida_cc(nombre):
            revista = "cc"
            ext_id = ext_id_cc
            ext_sec = ext_sec_cc
            const_bit = bitacora_cc
            proc_css = css_cc
        else:
            print(f"  [Ignorado] '{nombre}': No cumple formato RMDE ni CC.")
            continue

        revista_id = ext_id(nombre)
        clave_bitacora = const_bit(nombre)

        if revista_id is None or clave_bitacora is None:
            print(f"  [Aviso] No se pudo extraer ID de {nombre}, se omite.")
            errores += 1
            continue

        procesada_en_bitacora_nueva = clave_bitacora in ids_procesados
        procesada_en_bitacora_legacy = (
            revista_id in ids_procesados and clave_bitacora.endswith(":art")
        )

        if procesada_en_bitacora_nueva or procesada_en_bitacora_legacy:
            print(f"  [Omitida] {nombre} - ya procesada previamente.")
            omitidas += 1
            continue

        # Obtener procesador
        codigo_seccion = ext_sec(nombre)
        procesador_html_configurado = obtener_procesador_por_seccion(revista, codigo_seccion)

        # Generar subcarpeta contenedora (Salida/RMDE o Salida/CC)
        salida_revista_dir = os.path.join(SALIDA_DIR, revista.upper())

        # Ejecutar
        exito = procesar_carpeta_revista(
            nombre_carpeta=nombre, 
            ruta_carpeta=ruta, 
            procesador_css=proc_css, 
            procesador_html=procesador_html_configurado,
            salida_base=salida_revista_dir
        )

        if exito:
            registrar_en_bitacora(BITACORA_PATH, clave_bitacora)
            ids_procesados.append(clave_bitacora)
            procesadas += 1
            print(f"  [OK] {nombre} procesada correctamente en {revista.upper()}.")
        else:
            errores += 1
            print(f"  [Error] Fallo al procesar {nombre}.")

    duracion = time.time() - inicio
    print(f"\n{'=' * 60}")
    print("  Resumen del Lote:")
    print(f"     Procesadas: {procesadas}")
    print(f"     Omitidas:   {omitidas}")
    print(f"     Errores:    {errores}")
    print(f"     Tiempo:     {duracion:.2f} s")
    print("=" * 60)

if __name__ == "__main__":
    main()