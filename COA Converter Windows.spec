# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Windows build of COA Converter."""
import os
from PyInstaller.utils.hooks import collect_all

# --- Paths (relative to spec file location) ---
coa_converter_dir = os.path.join(os.path.dirname(SPECPATH), 'coa-converter')
if not os.path.isdir(coa_converter_dir):
    # Fallback: sibling directory in ~/tools/
    coa_converter_dir = os.path.join(os.path.expanduser('~'), 'tools', 'coa-converter')

datas = [
    ('src/styles/theme.qss', 'src/styles'),
    (os.path.join(coa_converter_dir, 'coa_converter.py'), 'coa_modules'),
    (os.path.join(coa_converter_dir, 'xlsx_filler.py'), 'coa_modules'),
    (os.path.join(coa_converter_dir, 'docx_filler.py'), 'coa_modules'),
    (os.path.join(coa_converter_dir, 'template_detector.py'), 'coa_modules'),
    (os.path.join(coa_converter_dir, 'supplier_checker.py'), 'coa_modules'),
    (os.path.join(coa_converter_dir, 'supplier_registry.json'), 'coa_modules'),
    (os.path.join(coa_converter_dir, 'templates'), 'coa_modules/templates'),
]
binaries = []
hiddenimports = [
    'pdfplumber', 'pdfplumber.page',
    'pdfminer', 'pdfminer.high_level',
    'pymupdf', 'fitz',
    'openpyxl', 'docx', 'anthropic',
    'PySide6', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets',
]

tmp_ret = collect_all('pdfplumber')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('openpyxl')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['src/main.py'],
    pathex=[coa_converter_dir],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='COA Converter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='COA Converter',
)
