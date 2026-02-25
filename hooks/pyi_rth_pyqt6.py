# PyQt6 runtime hook for PyInstaller
import os
import sys

# Ensure PyQt6 can find its plugins
from PyQt6 import QtCore

# Add PyQt6's plugin path to QT_PLUGIN_PATH
if hasattr(QtCore, 'QLibraryInfo'):
    try:
        plugin_path = QtCore.QLibraryInfo.path(QtCore.QLibraryInfo.LibraryPath.PluginsPath)
        if os.path.isdir(plugin_path):
            os.environ['QT_PLUGIN_PATH'] = plugin_path
            # Also add to sys.path for good measure
            if plugin_path not in sys.path:
                sys.path.append(plugin_path)
    except Exception:
        pass

# Workaround for PyInstaller not finding Qt6 DLLs on Windows
if sys.platform == 'win32':
    import ctypes
    import ctypes.util
    
    # Try to locate Qt6Core.dll
    try:
        # First, check if we're in a PyInstaller bundle
        if getattr(sys, 'frozen', False):
            # Look in the bundle directory
            bundle_dir = sys._MEIPASS
            qt_dll_dir = os.path.join(bundle_dir, 'PyQt6', 'Qt6', 'bin')
            if os.path.isdir(qt_dll_dir):
                os.environ['PATH'] = qt_dll_dir + os.pathsep + os.environ['PATH']
    except Exception:
        pass