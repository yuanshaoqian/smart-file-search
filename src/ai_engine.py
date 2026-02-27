#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 引擎模块
支持多种 AI 后端：Ollama、llama-cpp-python、llama.cpp CLI、以及智能回退模式
"""

import os
import re
import json
import time
import subprocess
import shutil
import urllib.request
import urllib.error
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

    def get_status(self) -> Dict[str, Any]:
        return {"available": self.is_available()}

    def close(self):
        pass


class OllamaBackend(AIBackend):
    """Ollama 后端 - 最简单的本地AI方案"""

    def __init__(self, config):
        super().__init__(config)
        self.model_name = "llama3.2:1b"  # 默认使用小模型
        self.api_url = "http://localhost:11434"
        self._available = None

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available

        try:
            # 检查 Ollama 服务是否运行
            req = urllib.request.Request(f"{self.api_url}/api/tags", method='GET')
            with urllib.request.urlopen(req, timeout=2) as response:
                if response.status == 200:
                    self.logger.info("Ollama 服务可用")
                    self._available = True
                    return True
        except (urllib.error.URLError, TimeoutError, ConnectionRefusedError):
            self.logger.debug("Ollama 服务未运行")
        except Exception as e:
            self.logger.debug(f"检查 Ollama 失败: {e}")

        # 检查 ollama 命令是否存在
        if shutil.which('ollama'):
            self.logger.info("找到 Ollama 命令，但服务未运行")
            self._available = False
            return False

        self._available = False
        return False

    def get_status(self) -> Dict[str, Any]:
        status = {"available": self.is_available(), "installed": shutil.which('ollama') is not None}

        if status["available"]:
            try:
                req = urllib.request.Request(f"{self.api_url}/api/tags", method='GET')
                with urllib.request.urlopen(req, timeout=2) as response:
                    data = json.loads(response.read().decode())
                    models = [m['name'] for m in data.get('models', [])]
                    status['models'] = models
                    if models:
                        self.model_name = models[0]  # 使用第一个可用模型
            except Exception:
                pass

        return status

    def load_model(self, model_path: Path) -> bool:
        # Ollama 不需要加载模型文件
        return self.is_available()

    def complete(self, prompt: str, max_tokens: int = 256, temperature: float = 0.7) -> Optional[str]:
        if not self.is_available():
            return None

        try:
            data = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature,
                }
            }

            req = urllib.request.Request(
                f"{self.api_url}/api/generate",
                data=json.dumps(data).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode())
                return result.get('response', '').strip()

        except Exception as e:
            self.logger.error(f"Ollama 推理失败: {e}")
            return None


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
    """智能后端 - 使用规则匹配和启发式方法，无需AI模型"""

    # 文件类型关键词映射
    FILE_TYPE_KEYWORDS = {
        '.pdf': ['pdf', 'PDF文档', '便携式文档'],
        '.docx': ['word', 'doc', 'docx', 'word文档', '微软文档'],
        '.doc': ['word', 'doc', 'word文档'],
        '.xlsx': ['excel', 'xlsx', 'xls', '表格', '电子表格'],
        '.xls': ['excel', 'xls', '表格'],
        '.pptx': ['ppt', 'pptx', 'powerpoint', '演示文稿', '幻灯片'],
        '.txt': ['txt', '文本', '记事本'],
        '.md': ['md', 'markdown', 'markdown文档'],
        '.py': ['py', 'python', 'python代码', 'python脚本'],
        '.java': ['java', 'java代码', 'java文件'],
        '.js': ['js', 'javascript', 'js代码'],
        '.html': ['html', '网页', 'web页面'],
        '.css': ['css', '样式表', '样式'],
        '.json': ['json', 'json文件', '配置文件'],
        '.xml': ['xml', 'xml文件'],
        '.zip': ['zip', '压缩包', '压缩文件'],
        '.rar': ['rar', '压缩包'],
        '.7z': ['7z', '压缩包'],
        '.mp3': ['mp3', '音乐', '音频'],
        '.mp4': ['mp4', '视频', '电影'],
        '.jpg': ['jpg', 'jpeg', '图片', '照片', '图像'],
        '.png': ['png', '图片', '照片'],
        '.gif': ['gif', '动图', '图片'],
    }

    # 时间关键词映射
    TIME_KEYWORDS = {
        '今天': 1,
        '今日': 1,
        '昨天': 2,
        '昨日': 2,
        '本周': 7,
        '这周': 7,
        '上周': 14,
        '最近一周': 7,
        '最近三天': 3,
        '最近七天': 7,
        '最近一月': 30,
        '最近一个月': 30,
        '本月': 30,
        '上个月': 60,
    }

    # 大小关键词映射 (MB)
    SIZE_KEYWORDS = {
        '大文件': 100,
        '超大': 500,
        '小文件': 0,
        '空文件': 0,
    }

    def __init__(self, config):
        super().__init__(config)
        self.logger.info("使用智能后端（规则匹配模式）")

    def is_available(self) -> bool:
        return True

    def load_model(self, model_path: Path) -> bool:
        return True

    def complete(self, prompt: str, max_tokens: int = 256, temperature: float = 0.7) -> Optional[str]:
        # 简单后端不进行文本生成
        return None

    def parse_query(self, query: str) -> QueryAnalysis:
        """智能解析查询"""
        query_lower = query.lower()
        keywords = []
        filters = {}
        intent_parts = []

        # 提取文件类型
        detected_extensions = []
        for ext, keywords_list in self.FILE_TYPE_KEYWORDS.items():
            for kw in keywords_list:
                if kw.lower() in query_lower:
                    detected_extensions.append(ext)
                    break

        if detected_extensions:
            filters['extensions'] = list(set(detected_extensions))
            intent_parts.append(f"文件类型: {', '.join(detected_extensions)}")

        # 提取时间范围
        for time_kw, days in self.TIME_KEYWORDS.items():
            if time_kw in query:
                from datetime import date, timedelta
                filters['modified_after'] = date.today() - timedelta(days=days)
                intent_parts.append(f"时间: {time_kw}")
                break

        # 提取大小条件
        for size_kw, size_mb in self.SIZE_KEYWORDS.items():
            if size_kw in query:
                if size_mb > 0:
                    filters['min_size'] = size_mb * 1024 * 1024
                intent_parts.append(f"大小: {size_kw}")
                break

        # 提取关键词（中文、英文、数字）
        # 移除已识别的特殊词汇
        clean_query = query
        for ext_list in self.FILE_TYPE_KEYWORDS.values():
            for kw in ext_list:
                clean_query = clean_query.replace(kw, '')
        for time_kw in self.TIME_KEYWORDS:
            clean_query = clean_query.replace(time_kw, '')
        for size_kw in self.SIZE_KEYWORDS:
            clean_query = clean_query.replace(size_kw, '')

        # 提取剩余关键词
        keywords = re.findall(r'[\u4e00-\u9fff\w]{2,}', clean_query)

        # 构建意图描述
        if intent_parts:
            intent = f"智能搜索 - {'; '.join(intent_parts)}"
        else:
            intent = f"关键词搜索"

        confidence = 0.7 if filters else 0.5

        return QueryAnalysis(
            keywords=keywords,
            filters=filters,
            intent=intent,
            confidence=confidence
        )


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
            ("ollama", OllamaBackend),
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

        # 回退到智能后端（始终可用）
        self.backend = SimpleBackend(self.config)
        self.backend_type = "simple"
        self.logger.info("AI 后端不可用，使用智能匹配模式")

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

        if self.backend_type in ("simple", "ollama"):
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
        if not self.enabled:
            return self._simple_parse(query)

        # 如果是智能后端，使用其智能解析
        if self.backend_type == "simple" and isinstance(self.backend, SimpleBackend):
            return self.backend.parse_query(query)

        if not self.model_loaded:
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
        # 使用智能后端的解析
        if isinstance(self.backend, SimpleBackend):
            return self.backend.parse_query(query)

        keywords = re.findall(r'[\u4e00-\u9fff\w]{2,}', query)

        filters = {}
        query_lower = query.lower()

        # 检测文件类型
        for ext, kws in SimpleBackend.FILE_TYPE_KEYWORDS.items():
            for kw in kws:
                if kw.lower() in query_lower:
                    filters['extensions'] = [ext]
                    break
            if 'extensions' in filters:
                break

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
        return self.enabled and (self.model_loaded or self.backend_type in ("simple", "ollama"))

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        info = {
            'enabled': self.enabled,
            'backend': self.backend_type,
            'model_loaded': self.model_loaded,
            'config_path': self.config.ai.model_path,
        }

        # 获取后端详细状态
        if self.backend:
            info['backend_status'] = self.backend.get_status()

        return info

    def get_available_backends(self) -> List[Dict[str, Any]]:
        """获取所有可用的AI后端列表"""
        backends_info = []

        # 检查 Ollama
        ollama = OllamaBackend(self.config)
        ollama_status = ollama.get_status()
        backends_info.append({
            'name': 'Ollama',
            'id': 'ollama',
            'available': ollama_status.get('available', False),
            'installed': ollama_status.get('installed', False),
            'models': ollama_status.get('models', []),
            'description': '本地AI服务，一键安装',
            'install_command': 'ollama pull llama3.2:1b',
            'website': 'https://ollama.ai'
        })

        # 检查 llama-cpp-python
        llama_cpp = LlamaCppPythonBackend(self.config)
        backends_info.append({
            'name': 'llama-cpp-python',
            'id': 'llama-cpp-python',
            'available': llama_cpp.is_available(),
            'installed': llama_cpp.is_available(),
            'description': 'Python绑定，需要编译',
            'install_command': 'pip install llama-cpp-python',
            'website': 'https://github.com/abetlen/llama-cpp-python'
        })

        # 检查 llama.cpp CLI
        llama_cli = LlamaCliBackend(self.config)
        backends_info.append({
            'name': 'llama.cpp CLI',
            'id': 'llama.cpp-cli',
            'available': llama_cli.is_available(),
            'installed': llama_cli.is_available(),
            'description': '命令行工具',
            'install_command': '下载预编译版本',
            'website': 'https://github.com/ggerganov/llama.cpp'
        })

        # 始终可用的智能模式
        backends_info.append({
            'name': '智能匹配',
            'id': 'simple',
            'available': True,
            'installed': True,
            'description': '内置智能匹配，无需安装',
            'install_command': None,
            'website': None
        })

        return backends_info

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
