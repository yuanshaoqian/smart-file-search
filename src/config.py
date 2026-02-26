#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
负责读取、验证和管理应用程序配置
"""

import os
import sys
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from loguru import logger

# 默认配置
DEFAULT_CONFIG = {
    "logging": {
        "level": "INFO",
        "file": "logs/app.log",
        "max_size": "10 MB",
        "retention": 7,
    },
    "index": {
        "directories": ["~/Documents", "~/Downloads"],
        "exclude_patterns": [
            "*.tmp",
            "*.log",
            "*.cache",
            "*.pyc",
            "__pycache__",
            ".git",
            ".DS_Store",
            "Thumbs.db",
        ],
        "max_file_size": 104857600,  # 100MB
        "supported_extensions": [
            ".txt",
            ".md",
            ".py",
            ".java",
            ".cpp",
            ".h",
            ".json",
            ".xml",
            ".yml",
            ".yaml",
            ".docx",
            ".xlsx",
        ],
        "index_dir": "data/indexdir",
        "update_interval": 300,
        "incremental": True,
    },
    "ai": {
        "enabled": False,
        "model_path": "data/models/llama-2-7b.Q4_K_M.gguf",
        "model_url": "https://huggingface.co/TheBloke/Llama-2-7B-GGUF/resolve/main/llama-2-7b.Q4_K_M.gguf",
        "context_size": 2048,
        "max_tokens": 512,
        "temperature": 0.1,
        "prompt_template": """你是一个文件搜索助手，请根据以下文件内容回答问题。

文件列表：
{file_context}

用户问题：{question}

请基于文件内容提供准确的回答。如果文件内容中没有相关信息，请如实说明。

回答：""",
    },
    "gui": {
        "theme": "dark",
        "font_family": "Microsoft YaHei, Segoe UI, sans-serif",
        "font_size": 12,
        "window_width": 1200,
        "window_height": 800,
        "max_results": 500,
        "preview_max_lines": 20,
        "preview_max_chars": 1000,
        "autocomplete_enabled": True,
        "autocomplete_max_items": 10,
        "sidebar_width": 250,
        "sidebar_visible": True,
    },
    "search": {
        "default_fields": ["filename", "content"],
        "fuzzy_enabled": True,
        "fuzzy_max_distance": 2,
        "wildcard_enabled": True,
        "phrase_enabled": True,
        "boolean_enabled": True,
    },
    "advanced": {
        "parser_threads": 4,
        "indexer_threads": 2,
        "cache_size_mb": 100,
        "watch_filesystem": True,
        "ignore_hidden": True,
        "skip_system_files": True,
    },
    "language": "zh_CN",
    "update_check": {
        "enabled": True,
        "interval_days": 7,
        "last_checked": None,
    },
}


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    file: str = "logs/app.log"
    max_size: str = "10 MB"
    retention: int = 7


@dataclass
class IndexConfig:
    """索引配置"""
    directories: List[str] = field(default_factory=lambda: ["~/Documents", "~/Downloads"])
    exclude_patterns: List[str] = field(default_factory=list)
    max_file_size: int = 104857600
    supported_extensions: List[str] = field(default_factory=list)
    index_dir: str = "data/indexdir"
    update_interval: int = 300
    incremental: bool = True


@dataclass
class AIConfig:
    """AI 配置"""
    enabled: bool = False
    model_path: str = "data/models/llama-2-7b.Q4_K_M.gguf"
    model_url: str = ""
    context_size: int = 2048
    max_tokens: int = 512
    temperature: float = 0.1
    prompt_template: str = ""


@dataclass
class GUIConfig:
    """GUI 配置"""
    theme: str = "dark"
    font_family: str = "Microsoft YaHei, Segoe UI, sans-serif"
    font_size: int = 12
    window_width: int = 1200
    window_height: int = 800
    max_results: int = 500
    preview_max_lines: int = 20
    preview_max_chars: int = 1000
    autocomplete_enabled: bool = True
    autocomplete_max_items: int = 10
    sidebar_width: int = 250
    sidebar_visible: bool = True


@dataclass
class SearchConfig:
    """搜索配置"""
    default_fields: List[str] = field(default_factory=lambda: ["filename", "content"])
    fuzzy_enabled: bool = True
    fuzzy_max_distance: int = 2
    wildcard_enabled: bool = True
    phrase_enabled: bool = True
    boolean_enabled: bool = True


@dataclass
class AdvancedConfig:
    """高级配置"""
    parser_threads: int = 4
    indexer_threads: int = 2
    cache_size_mb: int = 100
    watch_filesystem: bool = True
    ignore_hidden: bool = True
    skip_system_files: bool = True


@dataclass
class UpdateCheckConfig:
    """更新检查配置"""
    enabled: bool = True
    interval_days: int = 7
    last_checked: Optional[str] = None


@dataclass
class AppConfig:
    """应用程序配置"""
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    index: IndexConfig = field(default_factory=IndexConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    gui: GUIConfig = field(default_factory=GUIConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    advanced: AdvancedConfig = field(default_factory=AdvancedConfig)
    language: str = "zh_CN"
    update_check: UpdateCheckConfig = field(default_factory=UpdateCheckConfig)


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，如果为 None 则使用默认路径
        """
        self.config_path = config_path or self.get_default_config_path()
        self.config: Optional[AppConfig] = None
        self.logger = logger.bind(module="config")
        
    @staticmethod
    def get_default_config_path() -> str:
        """获取默认配置文件路径"""
        # 首先检查当前目录
        local_config = Path.cwd() / "config.yaml"
        if local_config.exists():
            return str(local_config)
        
        # 检查用户配置目录
        user_config_dir = Path.home() / ".config" / "smart-file-search"
        user_config_dir.mkdir(parents=True, exist_ok=True)
        user_config = user_config_dir / "config.yaml"
        
        return str(user_config)
    
    @staticmethod
    def expand_path(path: str) -> str:
        """展开路径中的 ~ 和变量"""
        return os.path.expanduser(os.path.expandvars(path))
    
    def load(self) -> AppConfig:
        """
        加载配置文件
        
        Returns:
            AppConfig: 配置对象
        """
        config_path = Path(self.config_path)
        
        # 如果配置文件不存在，创建默认配置
        if not config_path.exists():
            self.logger.warning(f"配置文件不存在: {config_path}，创建默认配置")
            self.create_default_config()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                yaml_config = yaml.safe_load(f) or {}
        except Exception as e:
            self.logger.error(f"读取配置文件失败: {e}")
            yaml_config = {}
        
        # 合并默认配置
        merged_config = self.merge_configs(DEFAULT_CONFIG, yaml_config)
        
        # 转换为数据类
        self.config = self.dict_to_dataclass(merged_config)
        
        # 验证配置
        self.validate_config()
        
        self.logger.info(f"配置加载成功: {config_path}")
        return self.config
    
    def merge_configs(self, default: Dict, user: Dict) -> Dict:
        """递归合并配置（用户配置覆盖默认配置）"""
        result = default.copy()
        
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def dict_to_dataclass(self, config_dict: Dict) -> AppConfig:
        """将字典转换为数据类"""
        # 处理嵌套配置
        logging_config = LoggingConfig(**config_dict.get("logging", {}))
        index_config = IndexConfig(**config_dict.get("index", {}))
        ai_config = AIConfig(**config_dict.get("ai", {}))
        gui_config = GUIConfig(**config_dict.get("gui", {}))
        search_config = SearchConfig(**config_dict.get("search", {}))
        advanced_config = AdvancedConfig(**config_dict.get("advanced", {}))
        update_check_config = UpdateCheckConfig(**config_dict.get("update_check", {}))
        
        # 展开路径
        index_config.directories = [self.expand_path(d) for d in index_config.directories]
        index_config.index_dir = self.expand_path(index_config.index_dir)
        ai_config.model_path = self.expand_path(ai_config.model_path)
        
        return AppConfig(
            logging=logging_config,
            index=index_config,
            ai=ai_config,
            gui=gui_config,
            search=search_config,
            advanced=advanced_config,
            language=config_dict.get("language", "zh_CN"),
            update_check=update_check_config,
        )
    
    def create_default_config(self) -> None:
        """创建默认配置文件"""
        config_path = Path(self.config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False, allow_unicode=True, indent=2)
            self.logger.info(f"创建默认配置文件: {config_path}")
        except Exception as e:
            self.logger.error(f"创建默认配置文件失败: {e}")
            raise
    
    def validate_config(self) -> None:
        """验证配置有效性"""
        if not self.config:
            return
        
        # 验证索引目录是否存在
        for dir_path in self.config.index.directories:
            expanded = Path(self.expand_path(dir_path))
            if not expanded.exists():
                self.logger.warning(f"索引目录不存在: {dir_path}")
        
        # 验证 AI 配置
        if self.config.ai.enabled:
            model_path = Path(self.expand_path(self.config.ai.model_path))
            if not model_path.exists():
                self.logger.warning(f"AI 模型文件不存在: {self.config.ai.model_path}")
    
    def save(self, config: Optional[AppConfig] = None) -> None:
        """
        保存配置到文件
        
        Args:
            config: 要保存的配置，如果为 None 则保存当前配置
        """
        if config is None:
            config = self.config
        
        if config is None:
            self.logger.error("没有配置可保存")
            return
        
        # 将数据类转换为字典
        config_dict = {
            "logging": config.logging.__dict__,
            "index": config.index.__dict__,
            "ai": config.ai.__dict__,
            "gui": config.gui.__dict__,
            "search": config.search.__dict__,
            "advanced": config.advanced.__dict__,
            "language": config.language,
            "update_check": config.update_check.__dict__,
        }
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True, indent=2)
            self.logger.info(f"配置已保存: {self.config_path}")
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
    
    def get_config(self) -> AppConfig:
        """获取配置（如果未加载则先加载）"""
        if self.config is None:
            self.load()
        return self.config


# 全局配置实例
_config_manager: Optional[ConfigManager] = None

def get_config(config_path: Optional[str] = None) -> AppConfig:
    """获取全局配置"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_path)
    return _config_manager.get_config()


def reload_config(config_path: Optional[str] = None) -> AppConfig:
    """重新加载配置"""
    global _config_manager
    _config_manager = ConfigManager(config_path)
    return _config_manager.load()


if __name__ == "__main__":
    # 测试配置加载
    config = get_config()
    print(f"日志级别: {config.logging.level}")
    print(f"索引目录: {config.index.directories}")
    print(f"AI 启用: {config.ai.enabled}")

def save_config(config: AppConfig, config_path: Optional[str] = None) -> None:
    """保存配置到文件"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_path)
    _config_manager.save(config)
