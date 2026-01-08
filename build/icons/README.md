# Icons Folder

Place your app icons here:

## Required Files

| File | Platform | Description |
|------|----------|-------------|
| `icon.png` | Source | 1024x1024 PNG (source image) |
| `icon.icns` | macOS | Apple icon format |
| `icon.ico` | Windows | Windows icon format |

## How to Create Icons

### From a PNG source (1024x1024):

**macOS (.icns):**
```bash
# Create iconset folder
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

# Convert to icns
iconutil -c icns icon.iconset

# Cleanup
rm -rf icon.iconset
```

**Windows (.ico):**

Option 1 - Online converter:
- https://cloudconvert.com/png-to-ico
- https://icoconvert.com/

Option 2 - ImageMagick:
```bash
# Install ImageMagick first
brew install imagemagick  # macOS
# or download from imagemagick.org for Windows

# Convert
convert icon.png -define icon:auto-resize=256,128,64,48,32,16 icon.ico
```

## Recommended Design

For a trading/finance app like Strategy Monitor:

- **Style**: Modern, minimal
- **Colors**: Dark theme compatible (works on dark backgrounds)
- **Elements**: Chart icon, price line, or abstract financial symbol
- **Avoid**: Too much detail (won't be visible at 16x16)

## Quick Placeholder

If you don't have an icon yet, the build will work without one.
You can add icons later and rebuild.
