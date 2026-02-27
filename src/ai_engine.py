#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 引擎模块
支持多种 AI 后端：llama-cpp-python、llama.cpp CLI、以及简单的回退模式
"""

import os
import re
import json
import time
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

from loguru import logger

from .config import get_config


@dataclass
class QueryAnalysis:
    """查询分析结果"""
    keywords: List[str]  # 关键词列表
    filters: Dict[str, Any]  # 过滤条件
    intent: str  # 用户意图
    confidence: float  # 置信度


class AIBackend:
    """AI 后端基类"""
    def __init__(self, config):
        self.config = config
        self.logger = logger.bind(module="ai_backend")

    def is_available(self) -> bool:
        raise NotImplementedError

    def load_model(self, model_path: Path) -> bool:
        raise NotImplementedError

    def complete(self, prompt: str, max_tokens: int = 256, temperature: float = 0.7) -> Optional[str]:
        raise NotImplementedError

    def close(self):
        pass


class LlamaCppPythonBackend(AIBackend):
    """llama-cpp-python 后端"""

    def __init__(self, config):
        super().__init__(config)
        self.model = None
        self.gpu_info = None

    def is_available(self) -> bool:
        try:
            import llama_cpp
            return True
        except ImportError:
            self.logger.info("llama-cpp-python 未安装")
            return False

    def _detect_gpu(self) -> dict:
        """检测可用的GPU"""
        gpu_info = {
            'available': False,
            'type': None,
            'device_count': 0,
            'n_gpu_layers': -1
        }

        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and result.stdout.strip():
                gpu_info['available'] = True
                gpu_info['type'] = 'cuda'
                gpu_info['device_count'] = len(result.stdout.strip().split('\n'))
                self.logger.info(f"检测到NVIDIA GPU")
                return gpu_info
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        try:
            import platform
            if platform.machine() == 'arm64':
                result = subprocess.run(['system_profiler', 'SPDisplaysDataType'],
                                      capture_output=True, text=True, timeout=2)
                if 'Metal' in result.stdout or 'Apple GPU' in result.stdout:
                    gpu_info['available'] = True
                    gpu_info['type'] = 'metal'
                    self.logger.info("检测到Apple Silicon GPU (Metal)")
                    return gpu_info
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return gpu_info

    def load_model(self, model_path: Path) -> bool:
        try:
            from llama_cpp import Llama

            self.logger.info(f"加载 AI 模型: {model_path}")
            self.gpu_info = self._detect_gpu()

            model_params = {
                'model_path': str(model_path),
                'n_ctx': self.config.ai.context_size,
                'n_threads': 4,
                'n_batch': 512,
                'verbose': False,
            }

            if self.gpu_info['available']:
                model_params['n_gpu_layers'] = self.gpu_info['n_gpu_layers']
                self.logger.info(f"启用GPU加速 ({self.gpu_info['type']})")
                if self.gpu_info['type'] == 'metal':
                    model_params['n_threads'] = 1

            self.model = Llama(**model_params)
            self.logger.info("AI 模型加载成功")
            return True

        except Exception as e:
            self.logger.error(f"加载 AI 模型失败: {e}")
            return False

    def complete(self, prompt: str, max_tokens: int = 256, temperature: float = 0.7) -> Optional[str]:
        if not self.model:
            return None

        try:
            response = self.model.create_completion(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["\n\n", "```"],
                echo=False,
            )
            if response:
                return response['choices'][0]['text'].strip()
        except Exception as e:
            self.logger.error(f"AI 推理失败: {e}")
        return None

    def close(self):
        self.model = None


class LlamaCliBackend(AIBackend):
    """llama.cpp CLI 后端 - 通过命令行调用"""

    def __init__(self, config):
        super().__init__(config)
        self.model_path = None
        self.cli_path = None
        self._find_llama_cli()

    def _find_llama_cli(self):
        """查找 llama.cpp 可执行文件"""
        candidates = ['llama-cli', 'main', 'llama']

        # 检查 PATH
        for cmd in candidates:
            if shutil.which(cmd):
                self.cli_path = shutil.which(cmd)
                self.logger.info(f"找到 llama.cpp CLI: {self.cli_path}")
                return

        # 检查常见位置
        common_paths = [
            Path.home() / '.local' / 'bin',
            Path('/usr/local/bin'),
            Path('/usr/bin'),
        ]

        for path in common_paths:
            for cmd in candidates:
                cli_file = path / cmd
                if cli_file.exists():
                    self.cli_path = str(cli_file)
                    self.logger.info(f"找到 llama.cpp CLI: {self.cli_path}")
                    return

    def is_available(self) -> bool:
        if self.cli_path:
            return True
        self.logger.info("llama.cpp CLI 未找到")
        return False

    def load_model(self, model_path: Path) -> bool:
        if not self.cli_path:
            return False
        self.model_path = model_path
        self.logger.info(f"配置 llama.cpp CLI 使用模型: {model_path}")
        return True

    def complete(self, prompt: str, max_tokens: int = 256, temperature: float = 0.7) -> Optional[str]:
        if not self.cli_path or not self.model_path:
            return None

        try:
            cmd = [
                self.cli_path,
                '-m', str(self.model_path),
                '-p', prompt,
                '-n', str(max_tokens),
                '--temp', str(temperature),
                '--no-display-prompt',
                '-c', str(self.config.ai.context_size),
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                self.logger.error(f"llama.cpp CLI 错误: {result.stderr}")

        except subprocess.TimeoutExpired:
            self.logger.error("llama.cpp CLI 超时")
        except Exception as e:
            self.logger.error(f"llama.cpp CLI 执行失败: {e}")

        return None


class SimpleBackend(AIBackend):
    """简单后端 - 不需要任何 AI 库，使用规则匹配"""

    def __init__(self, config):
        super().__init__(config)
        self.logger.info("使用简单后端（无 AI 模型）")

    def is_available(self) -> bool:
        return True

    def load_model(self, model_path: Path) -> bool:
        return True

    def complete(self, prompt: str, max_tokens: int = 256, temperature: float = 0.7) -> Optional[str]:
        # 简单后端不进行文本生成
        return None


class AIEngine:
    """AI 引擎 - 支持多种后端"""

    def __init__(self, config=None):
        """
        初始化 AI 引擎

        Args:
            config: 应用程序配置
        """
        self.config = config or get_config()
        self.logger = logger.bind(module="ai_engine")

        # AI 模型相关
        self.backend = None
        self.model_loaded = False
        self.enabled = self.config.ai.enabled
        self.backend_type = "none"

        # 线程池（用于异步处理）
        self.executor = ThreadPoolExecutor(max_workers=1)

        # 初始化后端
        if self.enabled:
            self._init_backend()

        # 初始化提示词模板
        self._init_prompt_templates()

    def _init_backend(self):
        """初始化 AI 后端"""
        # 按优先级尝试不同的后端
        backends = [
            ("llama-cpp-python", LlamaCppPythonBackend),
            ("llama.cpp-cli", LlamaCliBackend),
        ]

        for name, backend_class in backends:
            try:
                backend = backend_class(self.config)
                if backend.is_available():
                    self.backend = backend
                    self.backend_type = name
                    self.logger.info(f"使用 AI 后端: {name}")
                    return
            except Exception as e:
                self.logger.warning(f"初始化后端 {name} 失败: {e}")

        # 回退到简单后端
        self.backend = SimpleBackend(self.config)
        self.backend_type = "simple"
        self.logger.info("AI 后端不可用，使用简单模式")

    def _resolve_model_path(self) -> Optional[Path]:
        """解析模型路径"""
        import sys

        config_path = Path(self.config.ai.model_path).expanduser()
        candidates = []

        if config_path.is_absolute():
            candidates.append(config_path)
        else:
            if getattr(sys, 'frozen', False):
                exe_dir = Path(sys.executable).parent
                bundle_dir = Path(sys._MEIPASS)
                candidates.extend([
                    exe_dir / config_path,
                    bundle_dir / config_path,
                    bundle_dir / 'data' / 'models' / config_path.name,
                ])
            else:
                project_root = Path(__file__).parent.parent
                candidates.extend([
                    project_root / config_path,
                    project_root / 'data' / 'models' / config_path.name,
                ])
            candidates.append(config_path)

        for path in candidates:
            if path.exists() and path.is_file():
                self.logger.info(f"找到模型文件: {path}")
                return path

        self.logger.warning(f"模型文件未找到")
        return None

    def _load_model(self) -> bool:
        """加载 AI 模型"""
        if not self.enabled or not self.backend:
            return False

        if self.backend_type == "simple":
            return True

        model_path = self._resolve_model_path()
        if model_path is None:
            self.logger.error("模型文件不存在")
            return False

        if self.backend.load_model(model_path):
            self.model_loaded = True
            return True

        return False

    def _init_prompt_templates(self) -> None:
        """初始化提示词模板"""
        self.query_analysis_template = """分析用户查询，提取搜索关键词和过滤条件。

用户查询：{query}

请输出 JSON 格式：
{{"keywords": ["关键词"], "filters": {{"extensions": [".pdf"]}}, "intent": "意图", "confidence": 0.9}}"""

        self.answer_template = self.config.ai.prompt_template
        self.summary_template = """请为以下内容生成摘要：

{content}

摘要（不超过100字）："""

    def parse_natural_language(self, query: str) -> QueryAnalysis:
        """解析自然语言查询"""
        if not self.enabled or not self.model_loaded:
            return self._simple_parse(query)

        try:
            prompt = self.query_analysis_template.format(query=query)
            response = self.backend.complete(prompt, max_tokens=300, temperature=0.1)

            if response:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(0))
                    return QueryAnalysis(
                        keywords=data.get('keywords', []),
                        filters=data.get('filters', {}),
                        intent=data.get('intent', ''),
                        confidence=data.get('confidence', 0.5)
                    )
        except Exception as e:
            self.logger.error(f"AI 解析失败: {e}")

        return self._simple_parse(query)

    def _simple_parse(self, query: str) -> QueryAnalysis:
        """简单解析（回退方法）"""
        keywords = re.findall(r'[\u4e00-\u9fff\w]{2,}', query)

        filters = {}
        if 'pdf' in query.lower():
            filters['extensions'] = ['.pdf']
        if 'word' in query.lower() or 'doc' in query.lower():
            filters.setdefault('extensions', []).append('.docx')
        if 'excel' in query.lower() or 'xls' in query.lower():
            filters.setdefault('extensions', []).append('.xlsx')

        return QueryAnalysis(
            keywords=keywords,
            filters=filters,
            intent=f"搜索: {query}",
            confidence=0.6
        )

    def generate_answer(self, question: str, context_files: List[Dict[str, Any]]) -> str:
        """基于文件内容生成回答"""
        if not self.enabled or not self.model_loaded:
            return self._simple_answer(question, context_files)

        if not context_files:
            return "没有找到相关的文件内容来回答这个问题。"

        try:
            file_context = ""
            for i, file in enumerate(context_files[:5], 1):
                file_context += f"文件 {i}: {file.get('filename', '未知')}\n"
                if content := file.get('content_preview', ''):
                    file_context += f"内容: {content[:500]}\n"
                file_context += "-" * 40 + "\n"

            prompt = self.answer_template.format(
                file_context=file_context,
                question=question
            )

            response = self.backend.complete(
                prompt,
                max_tokens=self.config.ai.max_tokens,
                temperature=self.config.ai.temperature
            )

            if response:
                return response

        except Exception as e:
            self.logger.error(f"AI 生成回答失败: {e}")

        return self._simple_answer(question, context_files)

    def _simple_answer(self, question: str, context_files: List[Dict[str, Any]]) -> str:
        """简单回答（回退方法）"""
        if not context_files:
            return "没有找到相关的文件。"

        file_list = []
        for i, file in enumerate(context_files[:10], 1):
            filename = file.get('filename', '未知文件')
            size_mb = file.get('size', 0) / (1024 * 1024)
            file_list.append(f"{i}. {filename} ({size_mb:.1f} MB)")

        return f"找到 {len(context_files)} 个相关文件：\n\n" + "\n".join(file_list)

    def summarize_file(self, file_content: str, file_info: str = "") -> str:
        """生成文件摘要"""
        if not self.enabled or not self.model_loaded:
            return self._simple_summary(file_content)

        try:
            content = file_content[:3000]
            prompt = self.summary_template.format(content=content)
            response = self.backend.complete(prompt, max_tokens=200, temperature=0.2)

            if response:
                return response
        except Exception as e:
            self.logger.error(f"生成摘要失败: {e}")

        return self._simple_summary(file_content)

    def _simple_summary(self, file_content: str) -> str:
        """简单摘要（回退方法）"""
        lines = file_content.split('\n')
        summary = ' '.join(line.strip() for line in lines[:3] if line.strip())
        return summary[:200] + '...' if len(summary) > 200 else summary

    def is_enabled(self) -> bool:
        """检查 AI 功能是否启用"""
        return self.enabled and (self.model_loaded or self.backend_type == "simple")

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            'enabled': self.enabled,
            'backend': self.backend_type,
            'model_loaded': self.model_loaded,
            'config_path': self.config.ai.model_path,
        }

    def close(self) -> None:
        """关闭 AI 引擎"""
        if self.executor:
            self.executor.shutdown(wait=True)
        if self.backend:
            self.backend.close()
        self.model_loaded = False


# 全局 AI 引擎实例
_ai_engine_instance: Optional[AIEngine] = None

def get_ai_engine(config=None) -> AIEngine:
    """获取全局 AI 引擎"""
    global _ai_engine_instance
    if _ai_engine_instance is None:
        _ai_engine_instance = AIEngine(config)
    return _ai_engine_instance

def close_ai_engine() -> None:
    """关闭全局 AI 引擎"""
    global _ai_engine_instance
    if _ai_engine_instance:
        _ai_engine_instance.close()
        _ai_engine_instance = None
