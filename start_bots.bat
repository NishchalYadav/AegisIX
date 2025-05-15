@echo off
title AegisIX Multi-Bot System
color 0a

echo Checking Visual C++ Build Tools...
where cl >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing Visual C++ Build Tools...
    winget install Microsoft.VisualStudio.2022.BuildTools --silent --force
)

echo Creating data directories...
if not exist "data" mkdir data

echo Installing JavaScript dependencies...
call npm install --no-audit --no-fund --silent
call npm install jsonfile telegraf dotenv fs-extra moment --save

echo Installing Python dependencies...
python -m pip install --upgrade pip wheel setuptools
python -m pip install python-telegram-bot python-dotenv requests --no-deps
python -m pip install aiohttp --no-build-isolation

echo Starting AegisIX Multi-Bot System...
python run_bots.py
pause