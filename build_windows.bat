@echo off
title Construyendo Procesador RMDE para Windows
echo ========================================================
echo Iniciando compilacion de la aplicacion para Windows...
echo ========================================================

echo.
echo [0/3] Buscando Python 3 en el sistema...
:: Intentamos detectar python3 directamente
set PYTHON_CMD=python3
%PYTHON_CMD% --version >nul 2>&1
if %errorlevel% neq 0 (
    :: Si falla, intentamos usar el lanzador moderno de Windows
    set PYTHON_CMD=py -3
    %PYTHON_CMD% --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo ERROR FATAL: No se pudo encontrar Python 3 en este equipo.
        echo Asegurate de tener Python 3 instalado y agregado al PATH.
        pause
        exit /b
    )
)

echo Detectado con exito. Usando comando: %PYTHON_CMD%

echo.
echo [1/3] Instalando dependencias...
:: Usamos "-m pip" para asegurar que el pip pertenezca a Python 3 y no al viejo Python 2.7
%PYTHON_CMD% -m pip install -r requirements.txt
%PYTHON_CMD% -m pip install pyinstaller PySide6 Pillow

echo.
echo [2/3] Generando el ejecutable (.exe)...
:: Ejecutamos PyInstaller como modulo directamente desde Python 3
%PYTHON_CMD% -m PyInstaller --noconsole --onefile --icon=icono.ico --name "Formato Revistas" desktop_app.py
echo.
echo [3/3] Limpiando archivos temporales de compilacion...
rmdir /s /q build
del /q desktop_app.spec

echo.
echo ========================================================
echo COMPILACION TERMINADA CON EXITO.
echo Tu aplicacion esta en la carpeta "dist".
echo ========================================================
pause