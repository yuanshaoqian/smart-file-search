# -*- coding: utf-8 -*-
"""
PyInstaller hook for llama-cpp-python
Collects all necessary modules and binary dependencies
"""

import os
import sys

# Initialize empty collections
datas = []
binaries = []
hiddenimports = [
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

# Try to collect llama_cpp modules
try:
    from PyInstaller.utils.hooks import collect_all, collect_dynamic_libs

    try:
        ll_datas, ll_binaries, ll_hiddenimports = collect_all('llama_cpp')
        datas += ll_datas
        binaries += ll_binaries
        hiddenimports += ll_hiddenimports
        print(f"[hook-llama_cpp] collect_all: {len(ll_hiddenimports)} imports, {len(ll_binaries)} binaries")
    except Exception as e:
        print(f"[hook-llama_cpp] collect_all failed: {e}")

    try:
        dyn_datas, dyn_binaries, dyn_hiddenimports = collect_dynamic_libs('llama_cpp')
        datas += dyn_datas
        binaries += dyn_binaries
        hiddenimports += dyn_hiddenimports
        print(f"[hook-llama_cpp] collect_dynamic_libs: {len(dyn_binaries)} binaries")
    except Exception as e:
        print(f"[hook-llama_cpp] collect_dynamic_libs failed: {e}")

except ImportError as e:
    print(f"[hook-llama_cpp] PyInstaller hooks not available: {e}")

# Platform-specific binary collection
try:
    import llama_cpp
    package_dir = os.path.dirname(llama_cpp.__file__)
    print(f"[hook-llama_cpp] Package directory: {package_dir}")

    if sys.platform == 'win32':
        # Windows: Look for DLLs
        dll_locations = [
            package_dir,
            os.path.join(package_dir, 'lib'),
        ]
        dll_names = ['llama.dll', 'ggml.dll', 'ggml-base.dll', 'llama_shared.dll',
                     'libllama.dll', 'libggml.dll']

        for loc in dll_locations:
            if os.path.isdir(loc):
                for dll in dll_names:
                    dll_path = os.path.join(loc, dll)
                    if os.path.exists(dll_path):
                        binaries.append((dll_path, 'llama_cpp'))
                        print(f"[hook-llama_cpp] Found DLL: {dll_path}")

    elif sys.platform == 'darwin':
        # macOS: Look for dylibs
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                if file.endswith('.dylib') or file.endswith('.so'):
                    lib_path = os.path.join(root, file)
                    rel_dir = os.path.relpath(root, package_dir)
                    if rel_dir == '.':
                        rel_dir = 'llama_cpp'
                    else:
                        rel_dir = os.path.join('llama_cpp', rel_dir)
                    binaries.append((lib_path, rel_dir))
                    print(f"[hook-llama_cpp] Found dylib: {lib_path}")

    else:
        # Linux: Look for .so files
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                if file.endswith('.so') or '.so.' in file:
                    lib_path = os.path.join(root, file)
                    rel_dir = os.path.relpath(root, package_dir)
                    if rel_dir == '.':
                        rel_dir = 'llama_cpp'
                    else:
                        rel_dir = os.path.join('llama_cpp', rel_dir)
                    binaries.append((lib_path, rel_dir))
                    print(f"[hook-llama_cpp] Found .so: {lib_path}")

except ImportError:
    print("[hook-llama_cpp] llama_cpp not installed, skipping binary collection")
except Exception as e:
    print(f"[hook-llama_cpp] Error collecting binaries: {e}")

print(f"[hook-llama_cpp] Final: {len(hiddenimports)} imports, {len(binaries)} binaries, {len(datas)} data files")
