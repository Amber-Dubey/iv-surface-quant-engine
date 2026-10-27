@echo off
TITLE Quantitative IV Surface Engine
echo ==================================================
echo       LAUNCHING QUANTITATIVE IV SURFACE APP
echo ==================================================

:: Check if setup has been run
if not exist venv (
    echo [ERROR] Virtual environment 'venv' not found!
    echo Please run 'setup.bat' first before launching the app.
    pause
    exit /b
)

:: Activate environment and launch the GUI app
call venv\Scripts\activate
python gui_app.py