@echo off
setlocal

set "PYTHON_EXE="

python3 --version >nul 2>&1
if %errorlevel%==0 (
    set "PYTHON_EXE=python3"
) else (
    python --version >nul 2>&1
    if %errorlevel%==0 (
        set "PYTHON_EXE=python"
    )
)

if "%PYTHON_EXE%"=="" (
    echo No se encontro Python 3.12 o superior en PATH.
    echo Instala Python 3.12+ y asegurate de que python3 o python este en PATH.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('%PYTHON_EXE% --version') do set "PYVER=%%v"
for /f "tokens=1,2 delims=." %%a in ("%PYVER%") do (
    set "MAJOR=%%a"
    set "MINOR=%%b"
)

if not "%MAJOR%"=="3" (
    echo Se requiere Python 3.12 o superior. Version actual: %PYVER%
    pause
    exit /b 1
)

if %MINOR% LSS 12 (
    echo Se requiere Python 3.12 o superior. Version actual: %PYVER%
    pause
    exit /b 1
)

%PYTHON_EXE% -m pip install --upgrade pip
%PYTHON_EXE% -m pip install -r requirements.txt

%PYTHON_EXE% -m PyInstaller --clean --noconfirm --name "ProcesadorRMDE" --windowed desktop_app.py

endlocal
