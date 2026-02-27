# -*- coding: utf-8 -*-
"""
Runtime hook for llama-cpp-python
Ensures dynamic libraries can be found at runtime
"""

import os
import sys

def setup_llama_cpp_paths():
    """Setup library paths for llama-cpp-python"""
    # Check if we're running in a PyInstaller bundle
    if not getattr(sys, 'frozen', False):
        return

    bundle_dir = sys._MEIPASS
    llama_lib_dir = os.path.join(bundle_dir, 'llama_cpp', 'lib')

    # Add library directory to search paths
    if os.path.isdir(llama_lib_dir):
        # Add to DLL search path (Windows)
        if sys.platform == 'win32':
            try:
                os.add_dll_directory(llama_lib_dir)
            except (AttributeError, OSError):
                # Fallback for older Python versions
                os.environ['PATH'] = llama_lib_dir + os.pathsep + os.environ.get('PATH', '')

        # Set library path for Linux/macOS
        elif sys.platform == 'darwin':
            current_dyld = os.environ.get('DYLD_LIBRARY_PATH', '')
            if llama_lib_dir not in current_dyld:
                os.environ['DYLD_LIBRARY_PATH'] = llama_lib_dir + os.pathsep + current_dyld
        else:  # Linux
            current_ld = os.environ.get('LD_LIBRARY_PATH', '')
            if llama_lib_dir not in current_ld:
                os.environ['LD_LIBRARY_PATH'] = llama_lib_dir + os.pathsep + current_ld

    # Also check root bundle directory for libraries
    if sys.platform == 'win32':
        try:
            os.add_dll_directory(bundle_dir)
        except (AttributeError, OSError):
            pass

# Run setup on import
setup_llama_cpp_paths()
