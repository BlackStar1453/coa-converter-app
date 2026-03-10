# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('src/styles/theme.qss', 'src/styles'), ('/Users/cengyaohua/tools/coa-converter/coa_converter.py', 'coa_modules'), ('/Users/cengyaohua/tools/coa-converter/xlsx_filler.py', 'coa_modules'), ('/Users/cengyaohua/tools/coa-converter/docx_filler.py', 'coa_modules'), ('/Users/cengyaohua/tools/coa-converter/template_detector.py', 'coa_modules'), ('/Users/cengyaohua/tools/coa-converter/supplier_checker.py', 'coa_modules'), ('/Users/cengyaohua/tools/coa-converter/supplier_registry.json', 'coa_modules'), ('/Users/cengyaohua/tools/coa-converter/templates', 'coa_modules/templates')]
binaries = []
hiddenimports = ['pdfplumber', 'pdfplumber.page', 'pdfminer', 'pdfminer.high_level', 'pymupdf', 'fitz', 'openpyxl', 'docx', 'anthropic', 'PySide6', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets']
tmp_ret = collect_all('pdfplumber')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('openpyxl')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['src/main.py'],
    pathex=['/Users/cengyaohua/tools/coa-converter'],
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
    icon=['assets/icon.icns'],
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
app = BUNDLE(
    coll,
    name='COA Converter.app',
    icon='assets/icon.icns',
    bundle_identifier=None,
)
