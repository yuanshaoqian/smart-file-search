# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Smart File Search
Windows executable build configuration
"""

import os
import sys
from pathlib import Path

# Project root directory
project_root = Path(__file__).parent

# Application name
app_name = 'SmartFileSearch'

# Main script
main_script = str(project_root / 'src' / 'main.py')

# Python options
python_options = {
    'argv_emulation': False,
    'bootloader_ignore_signals': False,
    'debug': False,
    'strip': False,
    'optimize': 2,  # -O2 optimization
    'windowed': True,  # GUI application (no console)
}

# Add project root to sys.path for analysis
sys.path.insert(0, str(project_root))

# Data files to include
data_files = []

# Configuration files
config_files = [
    ('config.yaml', '.'),
    ('README.md', '.'),
    ('PROJECT_DESIGN.md', '.'),
    ('requirements.txt', '.'),
]

for src, dst in config_files:
    src_path = project_root / src
    if src_path.exists():
        data_files.append((str(src_path), dst))

# AI models directory
models_dir = project_root / 'data' / 'models'
if models_dir.exists():
    # Include all model files (GGUF format)
    for model_file in models_dir.glob('*.gguf'):
        data_files.append((str(model_file), 'data/models'))

# Include data directory structure
data_dirs = ['data/indexdir', 'data/logs', 'docs']
for rel_dir in data_dirs:
    dir_path = project_root / rel_dir
    if dir_path.exists():
        for root, dirs, files in os.walk(str(dir_path)):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for file in files:
                if not file.startswith('.'):
                    src_file = os.path.join(root, file)
                    # Destination path relative to data directory
                    dst_dir = os.path.relpath(root, str(project_root))
                    data_files.append((src_file, dst_dir))

# Hidden imports (packages that PyInstaller may miss)
hidden_imports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.QtNetwork',
    'PyQt6.QtWebEngineCore',
    'PyQt6.QtWebEngineWidgets',
    'PyQt6.sip',
    'whoosh',
    'whoosh.fields',
    'whoosh.index',
    'whoosh.qparser',
    'whoosh.analysis',
    'whoosh.support',
    'docx',
    'docx.opc',
    'docx.oxml',
    'docx.parts',
    'openpyxl',
    'openpyxl.workbook',
    'openpyxl.worksheet',
    'yaml',
    'loguru',
    'watchdog',
    'watchdog.observers',
    'watchdog.events',
    # llama-cpp-python AI engine
    'llama_cpp',
    'llama_cpp.llama',
    'llama_cpp.llama_types',
    'llama_cpp.llama_grammar',
    'llama_cpp.llama_cache',
    'llama_cpp.llama_chat_format',
    'llama_cpp.llama_speculative',
    'llama_cpp._internals',
    'llama_cpp._utils',
    # Other dependencies
    'chardet',
    'pandas',
    'magic',
    'sqlite3',
    'typing_extensions',
    'cached_property',
    'diskcache',
    'jinja2',
    'markupsafe',
]

# Hook directories
hookspath = [str(project_root / 'hooks')]

# Runtime hooks
runtime_hooks = [
    str(project_root / 'hooks' / 'pyi_rth_pyqt6.py'),
    str(project_root / 'hooks' / 'pyi_rth_llama_cpp.py'),
]

# Exclude modules to reduce size (keep numpy for llama-cpp-python)
excludes = [
    'scipy',
    'matplotlib',
    'pillow',
    'tkinter',
    'test',
    'unittest',
    'pydoc',
    'pdb',
    'setuptools',
    'pip',
    'wheel',
    'distutils',
    'ensurepip',
    'venv',
    'lib2to3',
]

# PyInstaller analysis
a = Analysis(
    [main_script],
    pathex=[str(project_root), str(project_root / 'src')],
    binaries=[],
    datas=data_files,
    hiddenimports=hidden_imports,
    hookspath=hookspath,
    runtime_hooks=runtime_hooks,
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# PyQt6 specific handling
pyqt6_packages = ['PyQt6']
for package in pyqt6_packages:
    # Collect Qt6 plugins
    try:
        import PyQt6
        qt_plugin_dir = os.path.join(os.path.dirname(PyQt6.__file__), 'Qt6', 'plugins')
        if os.path.isdir(qt_plugin_dir):
            # Add platform plugins
            a.datas.append((os.path.join(qt_plugin_dir, 'platforms', '*'), 'PyQt6/Qt6/plugins/platforms'))
            # Add image format plugins
            a.datas.append((os.path.join(qt_plugin_dir, 'imageformats', '*'), 'PyQt6/Qt6/plugins/imageformats'))
            # Add styles plugins
            a.datas.append((os.path.join(qt_plugin_dir, 'styles', '*'), 'PyQt6/Qt6/plugins/styles'))
    except ImportError:
        pass

# Add DLLs for Windows
if sys.platform == 'win32':
    # Add any necessary Windows DLLs
    pass

# Executable configuration
exe = EXE(
    a,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name=app_name,
    debug=False,
    strip=False,
    upx=True,  # Use UPX compression if available
    runtime_tmpdir=None,
    console=False,  # GUI application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path if available
)

# Collect extra files
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=app_name,
)