@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "VENV_PY=.venv\Scripts\python.exe"

if not exist ".venv\Scripts\python.exe" (
  where python >nul 2>nul
  if errorlevel 1 (
    echo [ERROR] Python was not found. Install Python 3.11 or 3.12, then run this file again.
    pause
    exit /b 1
  )
  echo [1/3] Creating the local Python environment...
  python -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Could not create .venv.
    pause
    exit /b 1
  )
)

echo [2/3] Installing required packages...
rem Ignore stale proxy environment variables and pip proxy settings for this run only.
set "HTTP_PROXY="
set "HTTPS_PROXY="
set "ALL_PROXY="
set "http_proxy="
set "https_proxy="
set "all_proxy="
set "NO_PROXY=*"
set "no_proxy=*"
set "PIP_PROXY="
set "PIP_CONFIG_FILE=NUL"

"%VENV_PY%" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
  echo.
  echo Official PyPI could not be reached. Trying the Tsinghua mirror...
  "%VENV_PY%" -m pip install --disable-pip-version-check -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
)

if errorlevel 1 (
  echo.
  echo [ERROR] Package installation failed. This is a network or proxy problem, not an app error.
  echo Try another network or run the mirror command shown in README.md.
  pause
  exit /b 1
)

"%VENV_PY%" -c "import fastapi, numpy, pandas, PIL, sklearn, skimage, scipy" >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Some required packages are still missing. Delete .venv and run this file again.
  pause
  exit /b 1
)

echo [3/3] Starting Jinxi Color Lens at http://127.0.0.1:7860
"%VENV_PY%" app.py
pause
