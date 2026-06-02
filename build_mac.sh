#!/bin/bash

echo "========================================================"
echo "Iniciando compilacion de la aplicacion para macOS..."
echo "========================================================"

echo "\n[0/3] Buscando Python 3 en el sistema..."
# Verificamos si el comando python3 existe en el sistema
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
    echo "Python 3 detectado con exito."
else
    echo "ERROR FATAL: No se encontro 'python3' en este equipo."
    echo "Asegurate de tener Python 3 instalado (puedes instalarlo desde python.org o usando Homebrew)."
    exit 1
fi

echo "\n[1/3] Instalando dependencias..."
# Usamos -m pip para garantizar que se instala en el Python 3 correcto
$PYTHON_CMD -m pip install -r requirements.txt
$PYTHON_CMD -m pip install pyinstaller PySide6 Pillow

echo "\n[2/3] Generando la aplicacion (.app)..."
# Ejecutamos PyInstaller como modulo nativo de Python 3
# --windowed asegura que se cree un paquete .app (App de Mac) y no un ejecutable de terminal
$PYTHON_CMD -m PyInstaller --windowed --onefile --icon=icono.icns --name "Formato Revistas" desktop_app.py
echo "\n[3/3] Limpiando archivos temporales..."
rm -rf build
rm -f desktop_app.spec

echo "\n========================================================"
echo "COMPILACION TERMINADA CON EXITO."
echo "Tu aplicacion 'desktop_app.app' esta en la carpeta 'dist'."
echo "========================================================"