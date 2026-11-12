@echo off
title Instalador de CBX Reader
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0install.ps1"
echo.
echo Presiona cualquier tecla para finalizar...
pause >nul
