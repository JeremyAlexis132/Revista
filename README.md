# Procesador de Revistas Academicas RMDE

Proyecto Python para procesar archivos HTML de revistas académicas exportados desde InDesign, reestructurándolos completamente al formato visual de la **Revista Mexicana de Derecho Electoral (RMDE)** publicada en [revistas.juridicas.unam.mx](https://revistas.juridicas.unam.mx/index.php/derecho-electoral/).

---

## Estructura del proyecto

```
revista_processor/
├── Archivos/               # Carpetas de revistas de entrada
│   └── 20462_rmde/         # Ejemplo de carpeta de revista
│       ├── css/
│       ├── image/
│       ├── *-web-resources/
│       │   ├── css/
│       │   └── image/
│       ├── 20462_rmde.html
│       └── .DS_Store        (ignorado)
│
├── Modules/
│   ├── __init__.py
│   ├── html_processor.py    # Extracción y reestructuración de HTML
│   ├── css_processor.py     # Procesamiento y corrección de CSS
│   └── utils.py             # Utilidades (bitácora, archivos, imágenes)
│
├── Salida/                  # Salida generada automáticamente
│   └── 20462_rmde/
│       ├── index.html       # HTML reestructurado
│       ├── css/             # Archivos CSS corregidos + referencia
│       └── images/          # Imágenes copiadas
│
├── main.py                  # Gestor principal
├── bitacora.json            # Registro de IDs procesados
├── requirements.txt         # Dependencias
└── README.md                # Este archivo
```

---

## Instalacion

### Requisitos

- Python 3.8 o superior
- pip

### Pasos

```bash
# Clonar o copiar el proyecto
cd revista_processor

# Instalar dependencias
pip install -r requirements.txt
```

---

## Uso

### 1. Preparar archivos de entrada

Coloque cada revista en una carpeta dentro de `Archivos/`. El nombre de la carpeta debe comenzar con el **ID numérico** de la revista:

```
Archivos/
├── 20462_rmde/
│   ├── 20462_rmde.html
│   ├── 20462_rmde-web-resources/
│   │   ├── css/
│   │   │   └── idGeneratedStyles.css
│   │   └── image/
│   │       ├── Gráfica1_editable.png
│   │       └── ...
│   └── .DS_Store (se ignora)
└── 20456_rmde/
    └── ...
```

### 2. Ejecutar el procesador

```bash
python main.py
```

### 3. Revisar la salida

Los archivos procesados se generan en `Salida/`:

```
Salida/
└── 20462_rmde/
    ├── index.html      # HTML reestructurado al formato RMDE
    ├── css/
    │   ├── idGeneratedStyles.css   # CSS original corregido
    │   └── referencia.css          # CSS adicional de referencia
    └── images/
        ├── Gráfica1_editable.png
        └── ...
```

---

## Bitacora de procesamiento

El archivo `bitacora.json` mantiene un registro de los IDs de revistas ya procesadas. Esto permite:

- **Evitar reprocesamiento**: Si una revista ya fue procesada, se omite automáticamente.
- **Procesamiento incremental**: Solo se procesan las revistas nuevas.
- **Persistencia**: Los IDs se acumulan sin borrar los anteriores.

### Formato

```json
["20462", "20456", "20500"]
```

### Reprocesar una revista

Para forzar el reprocesamiento de una revista, elimine su ID del archivo `bitacora.json` y ejecute `python main.py` de nuevo.

---

## Archivos no versionados

El repositorio está configurado para no versionar archivos temporales o generados automáticamente, por ejemplo:

- `Salida/` (resultado de cada ejecución)
- `bitacora.json` (estado local de procesamiento)
- `__pycache__/`, `*.pyc` y archivos de sistema como `.DS_Store`

Si desea limpiar la salida local antes de ejecutar nuevamente, puede eliminar el contenido de `Salida/` y reiniciar `bitacora.json`.

---

## Formato de archivos de entrada

### HTML de entrada

El HTML de entrada es exportado por **Adobe InDesign** y contiene clases CSS específicas:

| Clase CSS | Contenido |
|---|---|
| `identificador`, `identificadorfinal` | Metadatos de la revista (ISSN, DOI, etc.) |
| `tcc-final` | Título en español |
| `tcc-ingles` | Título en inglés |
| `autor_final_2apellidos` | Nombre del autor |
| `adscripcion` | Adscripción institucional / ORCID |
| `pais` | País del autor |
| `resumenfinal` | Resumen en español |
| `palabrasclave` | Palabras clave |
| `abstract_final` | Abstract en inglés |
| `keywords_final` | Keywords en inglés |
| `VV` (h3) | Títulos de sección principal |
| `IA` (h4) | Subtítulos |
| `pp`, `body_text` | Párrafos del cuerpo |
| `bib` | Referencias bibliográficas |
| `recepcion`, `publicacion` | Fechas |
| `como_citar` | Sección de cómo citar |
| `_idFootnotes` | Notas al pie |

### CSS de entrada

El CSS de InDesign usa valores absolutos (px) y colores transparentes (`#0000`) que se corrigen automáticamente:

- `#0000` → `#000000` (negro visible)
- Unidades `px` → `em` (proporcionales)
- Se agrega `referencia.css` con estilos de layout web

---

## Formato de referencia

El HTML generado replica la estructura visual de la página:

**https://revistas.juridicas.unam.mx/index.php/derecho-electoral/article/view/20456/20410**

### Características replicadas

- ✅ Contenedor principal con padding (`2em 3.5em`)
- ✅ Etiqueta flotante de tipo de artículo
- ✅ Identificadores de la revista en bloque superior
- ✅ Títulos en español e inglés con tipografía Garamond
- ✅ Autores con icono ORCID SVG inline
- ✅ Resumen, abstract, palabras clave y keywords
- ✅ Secciones con títulos en versalitas centrados
- ✅ Párrafos justificados con text-indent
- ✅ Tablas con bordes y estilos
- ✅ Imágenes/gráficas responsivas
- ✅ Referencias bibliográficas con hanging indent
- ✅ Notas al pie con enlaces bidireccionales
- ✅ Sección "Cómo citar" con formatos IIJ-UNAM, APA y RMDE

---

## Solucion de problemas

| Problema | Solución |
|---|---|
| No se encuentran archivos HTML | Verificar que la carpeta contenga un `.html` |
| Imágenes no aparecen | Verificar que existan en `image/` o `*-web-resources/image/` |
| CSS no se aplica | Verificar que los archivos CSS estén en la estructura esperada |
| Revista ya procesada | Eliminar su ID de `bitacora.json` |

---

## Licencia

Proyecto interno para procesamiento de revistas académicas del IIJ-UNAM.
