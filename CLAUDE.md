# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Running the Application
```bash
# Normal startup (Linux/macOS)
./start.sh

# Initialize/rebuild index on first run
./start.sh --init

# Debug mode with verbose logging
./start.sh --debug

# Direct Python execution
python -m src

# Windows startup
start.bat
```

### Building and Packaging
```bash
# Build portable package (Linux - creates tar.gz with all source)
./build_portable.sh

# Build Windows executable (Windows only)
pyinstaller build.spec --clean --noconfirm

# Create lightweight portable package (without AI model)
./build_lite.sh
```

### Testing
```bash
# Run tests (when tests/ directory exists)
pytest tests/

# Run specific test file
pytest tests/test_index.py
```

### Dependency Management
```bash
# Install core dependencies
pip install -r requirements.txt

# Install dependencies for exe build
pip install -r requirements-exe.txt

# Install macOS-specific dependencies
pip install -r requirements-mac.txt
```

## High-Level Architecture

### Core Application Flow

1. **Entry Point** (`src/main.py` or `src/__main__.py`):
   - Initializes PyQt6 application with splash screen
   - Loads configuration via `config.py`
   - Creates `FileIndexer` instance
   - Launches `MainWindow` GUI
   - AI module loads asynchronously if enabled

2. **Configuration System** (`src/config.py`):
   - Centralized YAML-based configuration management
   - Uses dataclasses for type-safe config access (`AppConfig`, `IndexConfig`, `AIConfig`, etc.)
   - Supports `~` expansion in paths
   - Falls back to defaults if config file missing
   - Global singleton pattern via `get_config()`

3. **Indexing Pipeline** (`src/index.py`):
   - `FileIndexer` class manages Whoosh full-text search index
   - Schema stores: path, filename, extension, size, modified, created, content, checksum
   - Incremental updates via checksum-based change detection
   - Multi-threaded file parsing using `ThreadPoolExecutor`
   - `create_index()` for full/rebuild, `search()` for queries

4. **File Parsing** (`src/file_parser.py`):
   - Abstract base class `FileParserBase` for extensible parsers
   - `TextFileParser`: Handles text files with chardet encoding detection
   - `WordDocumentParser`: Extracts text from .docx (requires python-docx)
   - `ExcelFileParser`: Extracts cell values from .xlsx/.xls (requires openpyxl)
   - `FileParser` facade dispatches to appropriate parser based on extension

5. **AI Engine** (`src/ai_engine.py`):
   - Optional Llama.cpp GGUF model integration for local AI inference
   - Falls back gracefully when model unavailable or disabled
   - `parse_natural_language()`: Converts queries to structured search filters
   - `generate_answer()`: RAG-style answers using retrieved file content
   - `summarize_file()`: Content summarization
   - Simple regex-based fallback when model not loaded

6. **GUI Architecture** (`src/gui.py`):
   - `MainWindow` extends QMainWindow with three-panel layout:
     - Top: Search input bar with history
     - Middle: AI answer display (rich text) + file results table
     - Right: Filter sidebar (file type, size, date)
   - `SettingsDialog` (`src/settings_dialog.py`): Built-in config editor
   - `SplashScreen` (`src/splash.py`): Loading screen with progress messages
   - Threading for search operations to keep UI responsive

### Key Data Structures

- **Whoosh Schema**: Fields defined in `FileIndexer.__init__()` - path (ID, unique), filename (TEXT), extension (KEYWORD), size (NUMERIC), modified/created (DATETIME), content (TEXT), checksum (ID)
- **FileMetadata** dataclass: Represents file information for indexing
- **QueryAnalysis** dataclass: AI-parsed query with keywords, filters, intent, confidence
- **Config dataclasses**: `AppConfig` contains nested `LoggingConfig`, `IndexConfig`, `AIConfig`, `GUIConfig`, `SearchConfig`, `AdvancedConfig`

### Global Singletons

The app uses global singletons accessed via getter functions:
- `get_config()` -> `AppConfig`
- `get_parser()` -> `FileParser`
- `get_indexer()` -> `FileIndexer`
- `get_ai_engine()` -> `AIEngine`

### Packaging Notes

- **PyInstaller spec**: `build.spec` - Windows executable build
- **Hook script**: `hooks/pyi_rth_pyqt6.py` - Fixes PyQt6 plugin paths in packaged exe
- **Portable packages**: Created by `build_portable.sh` (full) or `build_lite.sh` (without AI model)
- **AI model**: `data/models/phi-2.Q4_K_M.gguf` (~1.6GB, optional)
- **Index storage**: `data/indexdir/` - Whoosh index files

### Configuration File Structure

Key config sections to understand:
- `index.directories`: List of paths to index
- `index.supported_extensions`: File types to include
- `index.exclude_patterns`: Glob patterns to skip
- `ai.enabled`: Toggle AI features (requires model file)
- `ai.model_path`: Path to GGUF model file
- `gui.theme`: "dark" or "light" UI theme

### Development Patterns

1. **Adding new file format support**:
   - Create new parser class inheriting `FileParserBase`
   - Implement `parse()` and `supports()` methods
   - Register in `FileParser._register_parsers()`

2. **Adding new search filters**:
   - Extend Whoosh query logic in `FileIndexer.search()`
   - Add filter handling to GUI filter panel
   - Update AI prompt templates in `ai_engine.py` if natural language support needed

3. **GUI modifications**:
   - Main layout defined in `MainWindow.__init__()`
   - Connect signals to slots for event handling
   - Use QThread for long-running operations to prevent UI freeze

### Important Constraints

- **AI is optional**: All AI features must work when `ai.enabled=false` or model unavailable
- **Encoding handling**: Text files use chardet for detection; implement fallback encoding attempts
- **Thread safety**: Indexer uses AsyncWriter; GUI uses QThread for background operations
- **Path handling**: Always expand `~` in paths (use `config.py`'s `expand_path()` or `Path.expanduser()`)
- **File size limits**: Configurable via `index.max_file_size` (default 100MB)
