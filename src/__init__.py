#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart File Search - 智能文件搜索工具
"""

__version__ = "1.0.0"
__author__ = "Smart File Search Team"

from .config import get_config, ConfigManager
from .file_parser import get_parser
from .index import get_indexer
from .ai_engine import get_ai_engine

__all__ = [
    'get_config',
    'ConfigManager', 
    'get_parser',
    'get_indexer',
    'get_ai_engine',
]
