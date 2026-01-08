# 🏗️ Build & Distribution

Ce dossier contient tout le nécessaire pour créer les installateurs macOS et Windows.

## 📁 Structure

```
build/
├── README.md           # Ce fichier
├── build_macos.sh      # Script de build macOS
├── build_windows.bat   # Script de build Windows
├── strategy_monitor.spec  # Configuration PyInstaller
└── icons/
    ├── icon.icns       # Icône macOS
    ├── icon.ico        # Icône Windows
    └── icon.png        # Source (1024x1024)
```

## 🍎 Build macOS

### Prérequis
- macOS 10.15+
- Python 3.10+
- Virtual environment activé

### Commandes

```bash
# 1. Activer le venv
source venv/bin/activate

# 2. Installer les dépendances de build
pip install pyinstaller

# 3. Lancer le build
cd build
chmod +x build_macos.sh
./build_macos.sh
```

### Résultat
```
dist/
└── Strategy Monitor.app   # Application macOS
```

### Créer un DMG (optionnel)
```bash
# Installer create-dmg
brew install create-dmg

# Créer le DMG
./create_dmg.sh
```

---

## 🪟 Build Windows

### Prérequis
- Windows 10/11
- Python 3.10+
- Virtual environment activé

### Commandes

```cmd
REM 1. Activer le venv
venv\Scripts\activate

REM 2. Installer les dépendances de build
pip install pyinstaller

REM 3. Lancer le build
cd build
build_windows.bat
```

### Résultat
```
dist/
└── Strategy Monitor.exe   # Exécutable Windows
```

---

## 🎨 Icônes

### Créer les icônes depuis un PNG 1024x1024

**macOS (icns):**
```bash
# Créer iconset
mkdir icon.iconset
sips -z 16 16     icon.png --out icon.iconset/icon_16x16.png
sips -z 32 32     icon.png --out icon.iconset/icon_16x16@2x.png
sips -z 32 32     icon.png --out icon.iconset/icon_32x32.png
sips -z 64 64     icon.png --out icon.iconset/icon_32x32@2x.png
sips -z 128 128   icon.png --out icon.iconset/icon_128x128.png
sips -z 256 256   icon.png --out icon.iconset/icon_128x128@2x.png
sips -z 256 256   icon.png --out icon.iconset/icon_256x256.png
sips -z 512 512   icon.png --out icon.iconset/icon_256x256@2x.png
sips -z 512 512   icon.png --out icon.iconset/icon_512x512.png
sips -z 1024 1024 icon.png --out icon.iconset/icon_512x512@2x.png
iconutil -c icns icon.iconset
```

**Windows (ico):**
Utiliser un outil en ligne ou ImageMagick:
```bash
convert icon.png -define icon:auto-resize=256,128,64,48,32,16 icon.ico
```

---

## 🔐 Signature (Production)

### macOS - Notarisation Apple

Pour distribuer hors App Store:
1. Créer un compte Apple Developer ($99/an)
2. Générer un certificat "Developer ID Application"
3. Signer l'app:
```bash
codesign --force --deep --sign "Developer ID Application: VOTRE NOM" "dist/Strategy Monitor.app"
```
4. Notariser:
```bash
xcrun notarytool submit "Strategy Monitor.dmg" --apple-id "email" --password "app-specific-password" --team-id "TEAM_ID"
```

### Windows - Signature Code

1. Obtenir un certificat de signature (DigiCert, Sectigo, etc.)
2. Signer avec signtool:
```cmd
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com "Strategy Monitor.exe"
```

---

## 📦 Distribution

### Option 1: Fichier simple
- macOS: `.app` dans un `.zip`
- Windows: `.exe` dans un `.zip`

### Option 2: Installateur
- macOS: `.dmg` avec create-dmg
- Windows: `.msi` avec NSIS ou Inno Setup

### Option 3: Auto-update (avancé)
- Utiliser `pyupdater` ou service custom

---

## 🐛 Debugging

### L'app ne démarre pas?

1. Lancer depuis le terminal pour voir les erreurs:
```bash
# macOS
./dist/Strategy\ Monitor.app/Contents/MacOS/Strategy\ Monitor

# Windows
dist\Strategy Monitor.exe
```

2. Vérifier les imports manquants dans le `.spec`

3. Ajouter `--debug all` au build pour plus de logs

### Fichiers manquants?

Ajouter dans `datas` du `.spec`:
```python
datas=[
    ('assets', 'assets'),
    ('src/ui/styles', 'src/ui/styles'),
],
```
