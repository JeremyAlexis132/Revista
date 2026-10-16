#!/usr/bin/env python3
"""
Gestor principal del procesador de revistas académicas.
Procesa automáticamente todas las carpetas detectando a qué revista pertenecen
(RMDE, CC, RMDH, BMDC, Problema).

Para agregar una revista nueva: importar su utils y css_processor, y sumar una
entrada a REVISTAS (y al diccionario _REVISTAS de Modules/core/sections).
"""

import os
import sys
import time
from dataclasses import dataclass
from typing import Callable, List

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

from Modules.journals.rmde import utils as utils_rmde, css_processor as css_rmde
from Modules.journals.cc import utils as utils_cc, css_processor as css_cc
from Modules.journals.rmdh import utils as utils_rmdh, css_processor as css_rmdh
from Modules.journals.bmdc import utils as utils_bmdc, css_processor as css_bmdc
from Modules.journals.p import utils as utils_p, css_processor as css_p


@dataclass(frozen=True)
class Revista:
    """Funciones propias de cada revista que necesita el flujo genérico."""
    codigo: str                 # "rmde", "cc", ... (también define Salida/<CODIGO>)
    es_valida: Callable         # ¿la carpeta pertenece a esta revista?
    extraer_id: Callable
    extraer_seccion: Callable
    construir_clave: Callable   # clave que se guarda en bitacora.json
    procesar_css: Callable


def _revista(codigo: str, utils, css) -> Revista:
    return Revista(
        codigo=codigo,
        es_valida=utils.es_carpeta_valida,
        extraer_id=utils.extraer_id_de_carpeta,
        extraer_seccion=utils.extraer_codigo_seccion,
        construir_clave=utils.construir_clave_bitacora,
        procesar_css=css.procesar_y_combinar_css,
    )


# El orden importa: la primera revista cuya es_valida() acepte la carpeta gana.
REVISTAS: List[Revista] = [
    _revista("rmde", utils_rmde, css_rmde),
    _revista("cc", utils_cc, css_cc),
    _revista("rmdh", utils_rmdh, css_rmdh),
    _revista("bmdc", utils_bmdc, css_bmdc),
    _revista("p", utils_p, css_p),
]


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

def detectar_revista(nombre_carpeta: str):
    """Devuelve la Revista a la que pertenece la carpeta, o None."""
    for revista in REVISTAS:
        if revista.es_valida(nombre_carpeta):
            return revista
    return None

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
    
    # Crear la estructura dinámica en Salida/RMDE, Salida/CC, Salida/P, etc.
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
    nombres_revistas = ", ".join(r.codigo.upper() for r in REVISTAS)

    for nombre, ruta in carpetas:
        # Detectar la revista dinámicamente
        revista = detectar_revista(nombre)
        if revista is None:
            print(f"  [Ignorado] '{nombre}': No cumple formato de ninguna revista ({nombres_revistas}).")
            continue

        revista_id = revista.extraer_id(nombre)
        clave_bitacora = revista.construir_clave(nombre)

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
        codigo_seccion = revista.extraer_seccion(nombre)
        procesador_html_configurado = obtener_procesador_por_seccion(revista.codigo, codigo_seccion)

        # Generar subcarpeta contenedora
        salida_revista_dir = os.path.join(SALIDA_DIR, revista.codigo.upper())

        # Ejecutar
        exito = procesar_carpeta_revista(
            nombre_carpeta=nombre, 
            ruta_carpeta=ruta, 
            procesador_css=revista.procesar_css, 
            procesador_html=procesador_html_configurado,
            salida_base=salida_revista_dir
        )

        if exito:
            registrar_en_bitacora(BITACORA_PATH, clave_bitacora)
            ids_procesados.append(clave_bitacora)
            procesadas += 1
            print(f"  [OK] {nombre} procesada correctamente en {revista.codigo.upper()}.")
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