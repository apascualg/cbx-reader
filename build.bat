@echo off
title Compilar CBX Reader a ejecutable (.exe)
cd /d "%~dp0"
echo ========================================
echo   Compilando CBX-Reader.exe con PyInstaller
echo ========================================
echo.
pyinstaller --noconsole --onefile --icon="icon.ico" --add-data="icon.ico;." --add-data="Inter.ttf;." --name="CBX-Reader" reader.py
if %ERRORLEVEL% EQU 0 (
    echo.
    echo Moviendo ejecutable a la raiz del proyecto...
    move /y "dist\CBX-Reader.exe" "CBX-Reader.exe"
    rmdir /s /q "build"
    rmdir /s /q "dist"
    del /q "CBX-Reader.spec"
    echo.
    echo [OK] CBX-Reader.exe compilado con exito.
) else (
    echo.
    echo [ERROR] Hubo un problema durante la compilacion.
)
echo.
pause
