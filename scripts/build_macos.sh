#!/usr/bin/env bash
# Build COA Converter as a macOS .app using PyInstaller
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COA_CONVERTER_DIR="$HOME/tools/coa-converter"

cd "$PROJECT_DIR"

echo "=== Building COA Converter ==="

# Clean previous builds
rm -rf build/ dist/

# Activate venv (create if needed)
if [ ! -d ".venv" ]; then
    uv venv --python 3.12 .venv
    uv pip install --python .venv/bin/python -r requirements.txt
fi
source .venv/bin/activate
uv pip install --python .venv/bin/python pyinstaller

# Build with PyInstaller
.venv/bin/pyinstaller \
    --name "COA Converter" \
    --windowed \
    --onedir \
    --icon assets/icon.icns \
    --add-data "src/styles/theme.qss:src/styles" \
    --paths "$COA_CONVERTER_DIR" \
    --add-data "$COA_CONVERTER_DIR/coa_converter.py:coa_modules" \
    --add-data "$COA_CONVERTER_DIR/xlsx_filler.py:coa_modules" \
    --add-data "$COA_CONVERTER_DIR/docx_filler.py:coa_modules" \
    --add-data "$COA_CONVERTER_DIR/template_detector.py:coa_modules" \
    --add-data "$COA_CONVERTER_DIR/supplier_checker.py:coa_modules" \
    --add-data "$COA_CONVERTER_DIR/supplier_registry.json:coa_modules" \
    --add-data "$COA_CONVERTER_DIR/templates:coa_modules/templates" \
    --hidden-import pdfplumber \
    --hidden-import pdfplumber.page \
    --hidden-import pdfminer \
    --hidden-import pdfminer.high_level \
    --hidden-import pymupdf \
    --hidden-import fitz \
    --hidden-import openpyxl \
    --hidden-import docx \
    --hidden-import anthropic \
    --hidden-import PySide6 \
    --hidden-import PySide6.QtCore \
    --hidden-import PySide6.QtGui \
    --hidden-import PySide6.QtWidgets \
    --collect-all pdfplumber \
    --collect-all openpyxl \
    src/main.py

echo ""
echo "=== Build complete ==="
echo "App: dist/COA Converter/"
echo ""
echo "To test: open 'dist/COA Converter/COA Converter.app'"
