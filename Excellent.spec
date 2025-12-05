# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['frontend.py'],
    pathex=[],
    binaries=[
        ('.venv\\Lib\\site-packages\\pyzbar\\libiconv.dll', 'pyzbar'), 
        ('.venv\\Lib\\site-packages\\pyzbar\\libzbar-64.dll', 'pyzbar')
    ],
    datas=[
        ('fonts', 'fonts'), 
        ('app_icon.ico', '.'), 
        ('logo.png', '.'),
        ('Database', 'Database')
    ],
    hiddenimports=[
        'topdf', 
        'toexcel', 
        'fromqr',
        'invoices',
        'imports',
        'backend',
        'db',
        'backup',
        'rust_qr_backend',
        'pyzbar',
        'pyzbar.pyzbar',
        'pyzbar.pyzbar_error',
        'PIL',
        'PIL.Image',
        'flet',
        'flet_core',
        'xlsxwriter',
        'reportlab',
        'reportlab.lib',
        'reportlab.platypus',
        'reportlab.pdfgen',
        'reportlab.pdfbase',
        'reportlab.pdfbase.ttfonts',
        'sqlite3',
        'cv2',
        'numpy',
        'json',
        'datetime',
        'os',
        'sys',
        'shutil',
        'logging',
        'threading',
        'concurrent.futures'
    ],
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
    name='Excellent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['app_icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Excellent',
)
