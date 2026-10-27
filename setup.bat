@echo off
TITLE Setting up Quant IV Surface Engine...
echo ==================================================
echo    SETTING UP QUANTITATIVE IV SURFACE PIPELINE
echo ==================================================

echo [1/3] Creating Python Virtual Environment (venv)...
python -m venv venv

echo [2/3] Activating virtual environment & upgrading pip...
call venv\Scripts\activate
python -m pip install --upgrade pip

echo [3/3] Installing required Python packages...
if exist requirements.txt (
    pip install -r requirements.txt
) else (
    pip install yfinance pandas numpy
)

echo.
echo ==================================================
echo Setup complete! You can now double-click 'run.bat' 
echo to launch the app anytime.
echo ==================================================
pause