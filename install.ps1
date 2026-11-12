# Script de instalacion para CBX Reader
param (
    [switch]$Uninstall
)

$appName = "CBX Reader"
$installDir = [System.IO.Path]::Combine($env:LOCALAPPDATA, "Programs", "CBX-Reader")
$sourceDir = $PSScriptRoot

if ($Uninstall) {
    Write-Host "Desinstalando $appName..." -ForegroundColor Yellow

    $desktopLnk = [System.IO.Path]::Combine([Environment]::GetFolderPath('Desktop'), "$appName.lnk")
    if (Test-Path $desktopLnk) { Remove-Item $desktopLnk -Force -ErrorAction SilentlyContinue }

    $startMenuLnk = [System.IO.Path]::Combine([Environment]::GetFolderPath('StartMenu'), 'Programs', "$appName.lnk")
    if (Test-Path $startMenuLnk) { Remove-Item $startMenuLnk -Force -ErrorAction SilentlyContinue }

    $regUninstall = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\CBX-Reader"
    if (Test-Path $regUninstall) { Remove-Item $regUninstall -Recurse -Force -ErrorAction SilentlyContinue }

    $regAppPaths = "HKCU:\Software\Microsoft\Windows\CurrentVersion\App Paths\CBX-Reader.exe"
    if (Test-Path $regAppPaths) { Remove-Item $regAppPaths -Recurse -Force -ErrorAction SilentlyContinue }

    if (Test-Path $installDir) {
        Remove-Item $installDir -Recurse -Force -ErrorAction SilentlyContinue
    }

    Write-Host "$appName se ha desinstalado correctamente." -ForegroundColor Green
    return
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    Instalador de $appName" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Crear directorio de instalacion
if (-not (Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir -Force | Out-Null
}

# 2. Copiar archivos
Copy-Item (Join-Path $sourceDir "CBX-Reader.exe") (Join-Path $installDir "CBX-Reader.exe") -Force
Copy-Item (Join-Path $sourceDir "icon.ico") (Join-Path $installDir "icon.ico") -Force
if (Test-Path (Join-Path $sourceDir "Inter.ttf")) {
    Copy-Item (Join-Path $sourceDir "Inter.ttf") (Join-Path $installDir "Inter.ttf") -Force
}
if (Test-Path (Join-Path $sourceDir "README.md")) {
    Copy-Item (Join-Path $sourceDir "README.md") (Join-Path $installDir "README.md") -Force
}

# 3. Crear script de desinstalacion
$uninstallerBatLines = @(
    "@echo off",
    "powershell -ExecutionPolicy Bypass -File `"%~dp0install.ps1`" -Uninstall",
    "echo.",
    "echo Presiona cualquier tecla para finalizar...",
    "pause >nul"
)
$uninstallerBatContent = $uninstallerBatLines -join "`r`n"
[System.IO.File]::WriteAllText((Join-Path $installDir "Desinstalar.bat"), $uninstallerBatContent, [System.Text.Encoding]::ASCII)
Copy-Item (Join-Path $sourceDir "install.ps1") (Join-Path $installDir "install.ps1") -Force

# 4. Crear accesos directos (Escritorio y Menu Inicio)
$wsh = New-Object -ComObject WScript.Shell

$desktopPath = [Environment]::GetFolderPath('Desktop')
$shortcutDesktop = $wsh.CreateShortcut((Join-Path $desktopPath "$appName.lnk"))
$shortcutDesktop.TargetPath = (Join-Path $installDir "CBX-Reader.exe")
$shortcutDesktop.WorkingDirectory = $installDir
$shortcutDesktop.IconLocation = (Join-Path $installDir "icon.ico")
$shortcutDesktop.Description = "Lector de comics CBZ, CBR y ZIP con herramienta de recorte"
$shortcutDesktop.Save()

$startMenuPath = [System.IO.Path]::Combine([Environment]::GetFolderPath('StartMenu'), 'Programs')
$shortcutStart = $wsh.CreateShortcut((Join-Path $startMenuPath "$appName.lnk"))
$shortcutStart.TargetPath = (Join-Path $installDir "CBX-Reader.exe")
$shortcutStart.WorkingDirectory = $installDir
$shortcutStart.IconLocation = (Join-Path $installDir "icon.ico")
$shortcutStart.Description = "Lector de comics CBZ, CBR y ZIP con herramienta de recorte"
$shortcutStart.Save()

# 5. Registrar en Windows (Configuracion -> Aplicaciones instaladas)
$regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\CBX-Reader"
if (-not (Test-Path $regPath)) {
    New-Item -Path $regPath -Force | Out-Null
}
Set-ItemProperty -Path $regPath -Name "DisplayName" -Value "CBX Reader"
Set-ItemProperty -Path $regPath -Name "DisplayVersion" -Value "1.0.0"
Set-ItemProperty -Path $regPath -Name "Publisher" -Value "CBX Reader"
Set-ItemProperty -Path $regPath -Name "DisplayIcon" -Value (Join-Path $installDir "icon.ico")
Set-ItemProperty -Path $regPath -Name "InstallLocation" -Value $installDir
$desinstalarBatPath = Join-Path $installDir "Desinstalar.bat"
Set-ItemProperty -Path $regPath -Name "UninstallString" -Value "`"$desinstalarBatPath`""
Set-ItemProperty -Path $regPath -Name "NoModify" -Value 1 -Type DWord
Set-ItemProperty -Path $regPath -Name "NoRepair" -Value 1 -Type DWord

# 6. Registrar en App Paths (permite ejecutar "CBX-Reader" desde Win+R)
$appPaths = "HKCU:\Software\Microsoft\Windows\CurrentVersion\App Paths\CBX-Reader.exe"
if (-not (Test-Path $appPaths)) {
    New-Item -Path $appPaths -Force | Out-Null
}
Set-ItemProperty -Path $appPaths -Name "(Default)" -Value (Join-Path $installDir "CBX-Reader.exe")

Write-Host ""
Write-Host "[OK] Instalacion completada con exito!" -ForegroundColor Green
Write-Host " - Ejecutable instalado en: $installDir"
Write-Host " - Acceso directo creado en el Escritorio"
Write-Host " - Disponible en el Menu Inicio (busca 'CBX Reader')"
Write-Host " - Registrado en 'Aplicaciones instaladas' de Windows"
Write-Host ""
