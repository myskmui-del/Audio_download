@echo off
title Video/Audio Downloader - Starting...
cd /d "%~dp0"

echo Starting the app, please wait...
start "Downloader Server (keep this open)" cmd /k python app.py

echo Waiting for the server to start...
timeout /t 4 /nobreak >nul

echo Opening the site in your browser...
start "" http://127.0.0.1:5000

exit
