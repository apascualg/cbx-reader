@echo off
title Instalador de CBX Reader
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0install.ps1"
winget install CitrusSoda.ArcThumb
echo.
echo Presiona cualquier tecla para finalizar...
pause >nul
