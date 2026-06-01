#!/bin/bash
set -e

if ! command -v python3 >/dev/null 2>&1; then
  echo "No se encontro python3 en PATH. Instala Python 3.12+ y vuelve a intentar."
  exit 1
fi

PYVER=$(python3 -V | awk '{print $2}')
MAJOR=$(echo "$PYVER" | cut -d. -f1)
MINOR=$(echo "$PYVER" | cut -d. -f2)

if [ "$MAJOR" -ne 3 ] || [ "$MINOR" -lt 12 ]; then
  echo "Se requiere Python 3.12 o superior. Version actual: $PYVER"
  exit 1
fi

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

python3 -m PyInstaller --clean --noconfirm --name "ProcesadorRMDE" --windowed desktop_app.py
