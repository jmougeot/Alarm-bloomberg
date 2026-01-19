# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Strategy Monitor
Builds both macOS .app and Windows .exe
"""

import sys
import os
from pathlib import Path

# Chemin racine du projet
ROOT_DIR = Path(SPECPATH).parent.resolve()

# Debug: afficher les chemins
print(f"[SPEC] SPECPATH: {SPECPATH}")
print(f"[SPEC] ROOT_DIR: {ROOT_DIR}")

# Détection de la plateforme
IS_MACOS = sys.platform == 'darwin'
IS_WINDOWS = sys.platform == 'win32'

# Nom de l'application
APP_NAME = 'Strategy Monitor'
APP_VERSION = '3.2.1'

# Icônes - chemins absolus
ICON_MACOS = str(ROOT_DIR / 'build' / 'icons' / 'icon.icns')
ICON_WINDOWS = str(ROOT_DIR / 'build' / 'icons' / 'icon.ico')

# Debug: vérifier les icônes
print(f"[SPEC] ICON_WINDOWS: {ICON_WINDOWS} (exists: {os.path.exists(ICON_WINDOWS)})")
print(f"[SPEC] ICON_MACOS: {ICON_MACOS} (exists: {os.path.exists(ICON_MACOS)})")

# Point d'entrée
MAIN_SCRIPT = str(ROOT_DIR / 'main.py')

# Données à inclure
datas = [
    # Assets (sons, images)
    (str(ROOT_DIR / 'assets'), 'assets'),
]

# Fichiers cachés (hidden imports) - modules importés dynamiquement
hiddenimports = [
    # PySide6 essentials
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtNetwork',
    'PySide6.QtMultimedia',
    
    # WebSocket
    'websockets',
    'websockets.client',
    'websockets.server',
    
    # Async
    'asyncio',
    
    # Modules de l'app
    'src',
    'src.ui',
    'src.ui.main_window',
    # Widgets
    'src.ui.widgets',
    'src.ui.widgets.page_widget',
    'src.ui.widgets.sidebar_widget',
    'src.ui.widgets.strategy_block_widget',
    'src.ui.widgets.option_leg_widget',
    # Dialogs
    'src.ui.dialogs',
    'src.ui.dialogs.login_dialog',
    'src.ui.dialogs.group_dialog',
    'src.ui.dialogs.share_page_dialog',
    # Popups
    'src.ui.popups',
    'src.ui.popups.alert_popup',
    # Utils
    'src.ui.utils',
    'src.ui.utils.splash_screen',
    'src.ui.utils.async_worker',
    # Styles
    'src.ui.styles',
    'src.ui.styles.dark_theme',
    # Models
    'src.models',
    'src.models.page',
    'src.models.strategy',
    'src.models.name_to_strategy',
    # Services
    'src.services',
    'src.services.auth_service',
    'src.services.bloomberg_service',
    'src.services.server_service',
    'src.services.api_service',
    'src.services.settings_service',
    # Handlers
    'src.handlers',
    'src.handlers.file_handler',
    'src.handlers.alert_handler',
    'src.handlers.bloomberg_handler',
    'src.handlers.strategy_handler',
    'src.handlers.server_handler',
    'src.handlers.auth_handler',
    'src.config',
]

# Modules à exclure (réduire la taille)
excludes = [
    'tkinter',
    'matplotlib',
    'numpy',
    'pandas',
    'scipy',
    'PIL',
    'cv2',
    'torch',
    'tensorflow',
    'pytest',
    'unittest',
]

# Binaires à exclure
binaries_exclude = []

# Configuration de l'analyse
a = Analysis(
    [MAIN_SCRIPT],
    pathex=[str(ROOT_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

# Filtrer les binaires inutiles (optionnel, pour réduire la taille)
# a.binaries = [b for b in a.binaries if not any(x in b[0] for x in binaries_exclude)]

# Créer l'archive PYZ
pyz = PYZ(a.pure, a.zipped_data)

# Configuration selon la plateforme
if IS_MACOS:
    # === macOS: Créer un .app ===
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,  # Pas de terminal
        disable_windowed_traceback=False,
        argv_emulation=True,  # Important pour macOS
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=ICON_MACOS if os.path.exists(ICON_MACOS) else None,
    )
    
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name=APP_NAME,
    )
    
    app = BUNDLE(
        coll,
        name=f'{APP_NAME}.app',
        icon=ICON_MACOS if os.path.exists(ICON_MACOS) else None,
        bundle_identifier='com.bgc.strategymonitor',
        version=APP_VERSION,
        info_plist={
            'CFBundleName': APP_NAME,
            'CFBundleDisplayName': APP_NAME,
            'CFBundleVersion': APP_VERSION,
            'CFBundleShortVersionString': APP_VERSION,
            'CFBundleIdentifier': 'com.bgc.strategymonitor',
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '10.15.0',
            'NSRequiresAquaSystemAppearance': False,  # Support dark mode
        },
    )

else:
    # === Windows: Créer un .exe ===
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,  # Pas de console
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=ICON_WINDOWS if os.path.exists(ICON_WINDOWS) else None,
        version_file=None,  # Peut ajouter un fichier version.txt
    )
