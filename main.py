#!/usr/bin/env python3
"""
Gestor principal del procesador de revistas RMDE.

Escanea carpetas de entrada, procesa HTML/CSS/imagenes y genera salida.
"""

import os
import sys
import time

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

from Modules.css_processor import procesar_css
from Modules.sections import obtener_procesador_por_seccion
from Modules.utils import (
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
    """Resuelve carpeta de entrada con variantes de mayusculas/minusculas."""
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
    print("  Procesador de Revistas Academicas RMDE")
    print("  Formato de referencia: revistas.juridicas.unam.mx")
    print("=" * 60)
    print()


def escanear_carpetas() -> list:
    """Escanea carpeta de entrada y devuelve subcarpetas validas."""
    if not os.path.exists(ARCHIVOS_DIR):
        os.makedirs(ARCHIVOS_DIR, exist_ok=True)
        print(f"  Carpeta de entrada creada en: {ARCHIVOS_DIR}")
        return []

    carpetas = []
    for item in sorted(os.listdir(ARCHIVOS_DIR)):
        ruta = os.path.join(ARCHIVOS_DIR, item)
        if os.path.isdir(ruta) and not item.startswith("."):
            carpetas.append((item, ruta))

    return carpetas


def procesar_revista(nombre: str, ruta: str) -> bool:
    print(f"\n  Procesando: {nombre}")
    print(f"  {'-' * 50}")

    html_path = encontrar_html_en_carpeta(ruta)
    if html_path is None:
        print(f"    Error: no se encontro archivo HTML en {nombre}")
        return False
    print(f"    OK HTML encontrado: {os.path.basename(html_path)}")

    css_paths = encontrar_css_en_carpeta(ruta)
    if css_paths:
        print(f"    OK CSS encontrados: {len(css_paths)} archivo(s)")
    else:
        print("    Aviso: no se encontraron archivos CSS")

    rutas = crear_estructura_salida(SALIDA_DIR, nombre)
    print("    OK estructura de salida creada")

    archivos_css = procesar_css(css_paths, rutas["css"], nombre)

    imagenes = copiar_imagenes(ruta, rutas["images"])
    if imagenes:
        print(f"    OK imagenes copiadas: {len(imagenes)} archivo(s)")
    else:
        print("    Aviso: no se encontraron imagenes")

    codigo_seccion = extraer_codigo_seccion(nombre)
    procesador_html = obtener_procesador_por_seccion(codigo_seccion)

    return procesador_html(
        html_path=html_path,
        archivos_css=archivos_css,
        ruta_salida_html=rutas["html"],
        nombre_revista=nombre,
    )


def main() -> None:
    inicio = time.time()
    imprimir_banner()

    carpetas = escanear_carpetas()
    if not carpetas:
        print("  Aviso: no se encontraron carpetas de revistas")
        print(f"  Coloque las carpetas en: {ARCHIVOS_DIR}")
        return

    print(f"  Carpetas encontradas: {len(carpetas)}")

    ids_procesados = leer_bitacora(BITACORA_PATH)
    if ids_procesados:
        print(f"  Bitacora cargada: {', '.join(ids_procesados)}")
    else:
        print("  Bitacora vacia")

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
    print(f"     Procesadas:  {procesadas}")
    print(f"     Omitidas:    {omitidas}")
    print(f"     Errores:     {errores}")
    print(f"     Tiempo:      {duracion:.2f} segundos")
    print(f"     Salida en:   {SALIDA_DIR}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
