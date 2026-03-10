# Build COA Converter as a Windows .exe using PyInstaller
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$CoaDir = Join-Path $HOME "tools\coa-converter"

Set-Location $ProjectDir

Write-Host "=== Building COA Converter ==="

# Clean previous builds
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist")  { Remove-Item -Recurse -Force "dist" }

# Activate venv (create if needed)
if (-not (Test-Path ".venv")) {
    uv venv --python 3.12 .venv
    uv pip install --python .venv\Scripts\python.exe -r requirements.txt
}
& .venv\Scripts\Activate.ps1
pip install pyinstaller

# Build with PyInstaller
pyinstaller `
    --name "COA Converter" `
    --windowed `
    --onedir `
    --icon assets/icon.ico `
    --add-data "src/styles/theme.qss;src/styles" `
    --paths "$CoaDir" `
    --add-data "$CoaDir/coa_converter.py;coa_modules" `
    --add-data "$CoaDir/xlsx_filler.py;coa_modules" `
    --add-data "$CoaDir/docx_filler.py;coa_modules" `
    --add-data "$CoaDir/template_detector.py;coa_modules" `
    --add-data "$CoaDir/supplier_checker.py;coa_modules" `
    --add-data "$CoaDir/supplier_registry.json;coa_modules" `
    --add-data "$CoaDir/templates;coa_modules/templates" `
    --hidden-import pdfplumber `
    --hidden-import pdfplumber.page `
    --hidden-import pdfminer `
    --hidden-import pdfminer.high_level `
    --hidden-import pymupdf `
    --hidden-import fitz `
    --hidden-import openpyxl `
    --hidden-import docx `
    --hidden-import anthropic `
    --hidden-import PySide6 `
    --hidden-import PySide6.QtCore `
    --hidden-import PySide6.QtGui `
    --hidden-import PySide6.QtWidgets `
    --collect-all pdfplumber `
    --collect-all openpyxl `
    src/main.py

Write-Host ""
Write-Host "=== Build complete ==="
Write-Host "App: dist\COA Converter\"
Write-Host ""
Write-Host "To test: dist\COA Converter\COA Converter.exe"
