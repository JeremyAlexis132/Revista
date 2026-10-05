# Procesador de Revistas Académicas

Aplicación Python para procesar archivos HTML de revistas académicas exportados desde InDesign. El programa integra el HTML y el CSS, copia las imágenes y genera una versión lista para publicar de las revistas **RMDE**, **Cuestiones Constitucionales (CC)**, **Revista Mexicana de Historia del Derecho (RMDH)** y **Boletín Mexicano de Derecho Comparado (BMDC)**.

Incluye dos formas de uso:

- `main.py`: procesamiento por lotes desde la terminal.
- `desktop_app.py`: interfaz gráfica de escritorio.

## Requisitos

- Windows o macOS.
- **Python 3.10 o superior**. Se recomienda Python 3.12.
- `pip`, incluido normalmente con Python.

Comprueba la versión instalada con:

```bash
python --version
```

En macOS o en instalaciones donde el comando anterior no esté disponible, utiliza:

```bash
python3 --version
```

## Instalación del entorno virtual

Abre una terminal en la carpeta raíz del proyecto, la carpeta que contiene `main.py` y `requirements.txt`.

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Si tienes otra versión compatible instalada, sustituye `3.11` por esa versión, por ejemplo `py -3.10`.

Si PowerShell bloquea la activación de scripts, ejecuta PowerShell como usuario y aplica una sola vez:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Después vuelve a activar el entorno virtual.

### Windows CMD

```bat
py -3.11 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### macOS

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Cuando el entorno esté activo, la terminal mostrará normalmente `(.venv)` al inicio de la línea. Para salir del entorno ejecuta `deactivate`.

## Nombres y ubicación de las carpetas

### Procesamiento por terminal

Coloca las carpetas de revistas dentro de `archivos/` en la raíz del proyecto. También se acepta `Archivos/`, aunque se recomienda usar siempre el nombre en minúsculas:

```text
Revista/
├── archivos/
│   ├── 19943_cc-web-resources/
│   ├── 20213_rmde-web-resources/
│   └── 20308_bmdc-web-resources/
├── main.py
└── requirements.txt
```

El nombre de cada carpeta debe cumplir estas reglas:

- Comenzar con el ID numérico de la revista: `19943`, `20213`, etc.
- Contener el identificador de la revista: `_rmde`, `_cc`, `_rmhd` o `_bmdc`.
- Puede terminar en `-web-resources`, como en las exportaciones de InDesign.
- Se puede indicar el tipo de contenido entre el identificador de la revista y `-web-resources`.

Ejemplos válidos:

```text
19943_cc-web-resources
20213_rmde-web-resources
20308_rmde_nm-web-resources
20576_rmde_oe-web-resources
21139_bmdc-web-resources
```

### Códigos por tipo de revista

El código de la revista siempre va primero. El código opcional posterior identifica el tipo de contenido:

#### RMDE

```text
_rmde       Artículo
_rmde_nm    Nota metodológica
_rmde_ej    Estudio jurisprudencial
_rmde_ar    Análisis de reformas electorales
_rmde_oe    Observatorio electoral
```

Ejemplos:

```text
20213_rmde-web-resources
20308_rmde_nm-web-resources
20576_rmde_oe-web-resources
```

#### CC, RMDH y BMDC

Estas tres revistas utilizan los siguientes códigos generales:

```text
_cc   o   _rmhd   o   _bmdc   Artículo (también es el valor predeterminado)
_cj   Comentario jurisprudencial
_cl   Comentario legislativo
_rb   Reseña bibliográfica
_nm   Nota metodológica
_ej   Estudio jurisprudencial
_ar   Análisis de reformas electorales
_oe   Observatorio electoral
```

Ejemplos:

```text
30101_cc_cj-web-resources
30102_cc_rb-web-resources
20151_RMHD-web-resources
30103_bmdc_cl-web-resources
30104_bmdc_ej-web-resources
```

Si no se agrega un código de tipo, la carpeta se procesa como un artículo. Para un comentario genérico, debe elegirse el código correspondiente: `_cj` para comentario jurisprudencial o `_cl` para comentario legislativo.

Dentro de cada carpeta debe existir al menos un archivo `.html`. Los archivos `.css` pueden estar en la carpeta o en sus subcarpetas. Las imágenes se buscan en cualquier subcarpeta de recursos y se copian junto al `index.html` generado.

RMDH normaliza automáticamente las variantes de títulos de InDesign, autores, ORCID, adscripciones, correos electrónicos y declaraciones editoriales como uso de IA, conflicto de intereses, autoría y agradecimientos.

### Carpeta de salida

El procesamiento por terminal crea automáticamente `Salida/` y una subcarpeta por revista. Cada carpeta procesada contiene un `index.html` y las imágenes copiadas:

```text
Salida/
├── CC/19943_cc-web-resources/index.html
├── RMDH/20151_RMHD-web-resources/index.html
├── RMDE/20213_rmde-web-resources/index.html
└── BMDC/21139_bmdc-web-resources/index.html
```

La interfaz gráfica permite elegir las carpetas de entrada y la carpeta de salida manualmente; las reglas de nombres de las carpetas de entrada son las mismas.

Las salidas incluyen reglas responsive para pantallas pequeñas. Las tablas conservan su desplazamiento horizontal dentro de su propio contenedor y las imágenes se ajustan al ancho disponible en móvil.

## Uso

Con el entorno virtual activo, ejecuta una de estas opciones desde la raíz del proyecto.

### Procesamiento por terminal

```bash
python main.py
```

El programa procesa todas las carpetas válidas que encuentre en `archivos/` y registra las ya procesadas en `bitacora.json`.

### Interfaz gráfica

```bash
python desktop_app.py
```

Agrega las carpetas con **Buscar Carpeta...** o arrástralas a la aplicación, elige la carpeta de destino y pulsa **Procesar Archivos**.

## Generar un ejecutable

Con el entorno virtual activo y las dependencias instaladas:

- Windows: ejecuta `build_windows.bat`.
- macOS: ejecuta `bash build_mac.sh`.

El ejecutable o paquete generado se coloca en `dist/`. Los scripts de compilación instalan PyInstaller y PySide6 si todavía no están disponibles.

## Estructura principal del proyecto

```text
Revista/
├── archivos/              # Carpetas de entrada
├── Modules/               # Procesadores comunes y específicos por revista
├── Salida/                # Resultados generados
├── formatoCitacion/       # Estilos CSL de citación
├── main.py                # Procesamiento por terminal
├── desktop_app.py         # Interfaz gráfica
├── build_windows.bat      # Compilación para Windows
├── build_mac.sh           # Compilación para macOS
├── bitacora.json          # Registro de procesamiento
├── requirements.txt       # Dependencias Python
└── README.md              # Documentación
```