# -*- coding: utf-8 -*-
"""
PyInstaller hook for llama-cpp-python
Collects all necessary modules and binary dependencies
"""

import os
import sys
from PyInstaller.utils.hooks import collect_all, collect_dynamic_libs

# Collect all llama_cpp modules and data
datas, binaries, hiddenimports = collect_all('llama_cpp')

# Ensure all submodules are included
hiddenimports += [
    'llama_cpp',
    'llama_cpp.llama',
    'llama_cpp.llama_types',
    'llama_cpp.llama_grammar',
    'llama_cpp.llama_cache',
    'llama_cpp.llama_chat_format',
    'llama_cpp.llama_speculative',
    'llama_cpp._internals',
    'llama_cpp._utils',
]

# Collect dynamic libraries (libllama, etc.)
try:
    dyn_datas, dyn_binaries, dyn_hiddenimports = collect_dynamic_libs('llama_cpp')
    datas += dyn_datas
    binaries += dyn_binaries
    hiddenimports += dyn_hiddenimports
except Exception:
    pass

# Platform-specific handling
if sys.platform == 'win32':
    # Windows: Look for DLLs in package directory
    try:
        import llama_cpp
        package_dir = os.path.dirname(llama_cpp.__file__)

        # Common DLL names
        dll_names = ['llama.dll', 'ggml.dll', 'ggml-base.dll', 'llama_shared.dll']
        for dll in dll_names:
            dll_path = os.path.join(package_dir, 'lib', dll)
            if os.path.exists(dll_path):
                binaries.append((dll_path, 'llama_cpp/lib'))

        # Also check for CUDA DLLs
        cuda_dlls = ['cublas.dll', 'cublasLt.dll', 'cudart.dll']
        for dll in cuda_dlls:
            if os.path.exists(dll_path := os.path.join(package_dir, dll)):
                binaries.append((dll_path, 'llama_cpp'))
    except ImportError:
        pass

elif sys.platform == 'darwin':
    # macOS: Look for dylibs
    try:
        import llama_cpp
        package_dir = os.path.dirname(llama_cpp.__file__)

        # Look for .dylib files
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                if file.endswith('.dylib'):
                    lib_path = os.path.join(root, file)
                    rel_path = os.path.relpath(root, package_dir)
                    binaries.append((lib_path, os.path.join('llama_cpp', rel_path)))
    except ImportError:
        pass

else:
    # Linux: Look for .so files
    try:
        import llama_cpp
        package_dir = os.path.dirname(llama_cpp.__file__)

        # Look for .so files
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                if file.endswith('.so') or '.so.' in file:
                    lib_path = os.path.join(root, file)
                    rel_path = os.path.relpath(root, package_dir)
                    binaries.append((lib_path, os.path.join('llama_cpp', rel_path)))
    except ImportError:
        pass

print(f"[hook-llama_cpp] Collected {len(hiddenimports)} hidden imports")
print(f"[hook-llama_cpp] Collected {len(binaries)} binaries")
print(f"[hook-llama_cpp] Collected {len(datas)} data files")
