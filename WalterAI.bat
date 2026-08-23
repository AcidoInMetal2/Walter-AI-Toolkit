@echo off
REM ============================================================
REM  Walter AI Toolkit - Lanzador
REM  Doble clic para abrir la app, sin tener que usar cmd a mano.
REM ============================================================

REM Nos aseguramos de estar parados en la carpeta donde vive este
REM archivo .bat, sin importar desde dónde se haga doble clic.
cd /d "%~dp0"

call venv\Scripts\activate.bat

python launcher.py

REM Si la app se cerró con un error (crash), dejamos la ventana
REM abierta para poder leer el mensaje. Si se cerró normal, la
REM ventana de cmd se cierra sola.
if errorlevel 1 (
    echo.
    echo La aplicacion se cerro con un error. Revisa el mensaje de arriba.
    pause
)
