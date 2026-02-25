#!/bin/bash
# Smart File Search Portable Packaging Script for Linux
# This script prepares a portable package for Windows (source + models)
# The actual Windows .exe should be built on Windows using the provided scripts.

set -e  # Exit on error

# Configuration
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="SmartFileSearch"
VERSION="1.0.0"
BUILD_DIR="$PROJECT_ROOT/build"
PORTABLE_DIR="$BUILD_DIR/portable/$APP_NAME"
OUTPUT_FILE="$BUILD_DIR/${APP_NAME}-portable-v${VERSION}.tar.gz"

echo "=== Smart File Search Portable Packaging ==="
echo "Project root: $PROJECT_ROOT"
echo "Build directory: $BUILD_DIR"
echo "Output file: $OUTPUT_FILE"
echo

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf "$BUILD_DIR/portable"
mkdir -p "$PORTABLE_DIR"

# Copy source code
echo "Copying source code..."
cp -r "$PROJECT_ROOT/src" "$PORTABLE_DIR/"
cp "$PROJECT_ROOT/config.yaml" "$PORTABLE_DIR/"
cp "$PROJECT_ROOT/README.md" "$PORTABLE_DIR/"
cp "$PROJECT_ROOT/PROJECT_DESIGN.md" "$PORTABLE_DIR/"
cp "$PROJECT_ROOT/requirements.txt" "$PORTABLE_DIR/"
cp "$PROJECT_ROOT/requirements-exe.txt" "$PORTABLE_DIR/"
cp "$PROJECT_ROOT/build.spec" "$PORTABLE_DIR/"
cp "$PROJECT_ROOT/installer.iss" "$PORTABLE_DIR/"

# Copy documentation
if [ -d "$PROJECT_ROOT/docs" ]; then
    cp -r "$PROJECT_ROOT/docs" "$PORTABLE_DIR/"
fi

# Copy hooks directory
if [ -d "$PROJECT_ROOT/hooks" ]; then
    cp -r "$PROJECT_ROOT/hooks" "$PORTABLE_DIR/"
fi

# Copy data directory (including models)
echo "Copying data directory..."
mkdir -p "$PORTABLE_DIR/data"
if [ -d "$PROJECT_ROOT/data" ]; then
    cp -r "$PROJECT_ROOT/data"/* "$PORTABLE_DIR/data/"
fi

# Create Windows batch script for building
echo "Creating Windows build script..."
cat > "$PORTABLE_DIR/build_windows.bat" << 'EOF'
@echo off
REM Build script for Smart File Search on Windows
echo Smart File Search Windows Build Script
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.8+ from https://python.org
    exit /b 1
)

REM Check PyInstaller
pip list | findstr PyInstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller and dependencies...
    pip install -r requirements-exe.txt
) else (
    echo PyInstaller already installed.
)

echo.
echo Building executable with PyInstaller...
pyinstaller build.spec --clean --noconfirm

if errorlevel 1 (
    echo Build failed!
    exit /b 1
)

echo Build successful! Executable is in dist/SmartFileSearch/
echo.
echo To create an installer, install Inno Setup and compile installer.iss
echo.

pause
EOF

# Create Linux build script for reference
echo "Creating Linux build script..."
cat > "$PORTABLE_DIR/build_linux.sh" << 'EOF'
#!/bin/bash
# Linux build script for Smart File Search (for reference)
# Note: Windows executable cannot be built directly on Linux
# This script is for testing the application in Linux environment

set -e
echo "Linux build script - for development only"
pip install -r requirements.txt
python -m src.main --help
EOF
chmod +x "$PORTABLE_DIR/build_linux.sh"

# Create README for portable package
echo "Creating README..."
cat > "$PORTABLE_DIR/README-PORTABLE.md" << 'EOF'
# Smart File Search Portable Package

This package contains the Smart File Search application source code, configuration files, and AI models. You can build the Windows executable from this package.

## Contents

- `src/` - Python source code
- `data/` - Data directory including AI models (phi-2.Q4_K_M.gguf, ~1.6GB)
- `config.yaml` - Configuration file
- `requirements.txt` - Python dependencies
- `requirements-exe.txt` - Dependencies for Windows executable build
- `build.spec` - PyInstaller configuration
- `installer.iss` - Inno Setup installer script
- `hooks/` - PyInstaller runtime hooks
- `build_windows.bat` - Windows build script
- `build_linux.sh` - Linux build script (development)

## Building on Windows

### Prerequisites

1. Install Python 3.8+ from [python.org](https://python.org)
2. Add Python to PATH during installation
3. Install Microsoft Visual C++ Redistributable (may be required for llama-cpp-python)

### Steps

1. Extract this package to a folder (e.g., `C:\SmartFileSearch`)
2. Open Command Prompt as Administrator (optional)
3. Navigate to the extracted folder:
   ```
   cd C:\SmartFileSearch
   ```
4. Run the build script:
   ```
   build_windows.bat
   ```
5. The executable will be created in `dist/SmartFileSearch/` directory

### Creating an Installer

1. Install Inno Setup from [jrsoftware.org](https://jrsoftware.org/isdl.php)
2. Open `installer.iss` in Inno Setup Compiler
3. Click "Compile" to generate the installer

## Running from Source (Development)

If you have Python installed, you can run the application directly:

```
pip install -r requirements.txt
python -m src.main
```

## AI Model

The package includes the Phi-2 2.7B Q4_K_M GGUF model (~1.6GB). To use AI features:

1. Enable AI in config.yaml: set `ai.enabled: true`
2. Ensure the model path points to `data/models/phi-2.Q4_K_M.gguf`
3. The application will load the model on first AI query (may take a minute)

## Notes

- The first index creation may take time depending on the number of files
- AI features require significant RAM (8GB+ recommended)
- For best performance, exclude large directories in config.yaml

## Troubleshooting

- If build fails, ensure all dependencies are installed: `pip install -r requirements-exe.txt`
- If PyQt6 fails to load, try installing Visual C++ Redistributable
- For AI model issues, check that the model file exists and is not corrupted

EOF

# Create compressed archive
echo "Creating compressed archive..."
cd "$BUILD_DIR/portable"
tar -czf "$OUTPUT_FILE" "$APP_NAME"

# Calculate size
SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
echo
echo "=== Package Created Successfully ==="
echo "Output file: $OUTPUT_FILE"
echo "Size: $SIZE"
echo
echo "To deploy on Windows:"
echo "1. Copy the tar.gz file to a Windows machine"
echo "2. Extract using 7-Zip or similar tool"
echo "3. Follow instructions in README-PORTABLE.md"
echo
echo "Package contents:"
tree -L 3 "$PORTABLE_DIR" 2>/dev/null || find "$PORTABLE_DIR" -type f | head -20