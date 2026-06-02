# Procesador de Revistas Académicas RMDE

Proyecto Python para procesar archivos HTML de revistas académicas exportados desde InDesign, reestructurándolos completamente al formato visual de la **Revista Mexicana de Derecho Electoral (RMDE)** publicada en [revistas.juridicas.unam.mx](https://revistas.juridicas.unam.mx/index.php/derecho-electoral/).

El proyecto incluye tanto una herramienta de terminal (`main.py`) como una interfaz gráfica de escritorio (`desktop_app.py`) con soporte multiplataforma.

---

## Estructura del proyecto

```text
revista_processor/
├── Archivos/               # Carpetas de revistas de entrada (Terminal)
├── Modules/
│   ├── __init__.py
│   ├── html_processor.py   # Extracción y reestructuración de HTML
│   ├── css_processor.py    # Procesamiento y corrección de CSS
│   └── utils.py            # Utilidades (bitácora, archivos, imágenes)
│
├── Salida/                 # Salida generada automáticamente
├── main.py                 # Gestor principal por línea de comandos
├── desktop_app.py          # Aplicación de Escritorio (UI Visual)
├── build_windows.bat       # Compilador de ejecutable (.exe) para Windows
├── build_mac.sh            # Compilador de aplicación (.app) para macOS
├── bitacora.json           # Registro de IDs procesados
├── requirements.txt        # Dependencias
└── README.md               # Este archivo