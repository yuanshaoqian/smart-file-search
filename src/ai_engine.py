#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 引擎模块
基于 llama.cpp 的本地 AI 推理，支持自然语言理解和生成
"""

import os
import re
import json
import time
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


class AIEngine:
    """AI 引擎"""

    def __init__(self, config=None):
        """
        初始化 AI 引擎

        Args:
            config: 应用程序配置
        """
        self.config = config or get_config()
        self.logger = logger.bind(module="ai_engine")

        # AI 模型相关
        self.model = None
        self.model_loaded = False
        self.enabled = self.config.ai.enabled

        # GPU信息
        self.gpu_info = None

        # 线程池（用于异步处理）
        self.executor = ThreadPoolExecutor(max_workers=1)

        # 加载模型（如果启用）
        if self.enabled:
            self._load_model()

        # 初始化提示词模板
        self._init_prompt_templates()
    
    def _detect_gpu(self) -> dict:
        """检测可用的GPU"""
        gpu_info = {
            'available': False,
            'type': None,
            'device_count': 0,
            'n_gpu_layers': -1  # -1 表示所有层都放到GPU
        }

        try:
            # 检查CUDA (NVIDIA)
            import subprocess
            result = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and result.stdout.strip():
                gpu_info['available'] = True
                gpu_info['type'] = 'cuda'
                gpu_info['device_count'] = len(result.stdout.strip().split('\n'))
                gpu_names = result.stdout.strip().replace('\n', ', ')
                self.logger.info(f"检测到NVIDIA GPU: {gpu_names}")
                return gpu_info
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        try:
            # 检查ROCm (AMD)
            result = subprocess.run(['rocm-smi', '--showid'],
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                gpu_info['available'] = True
                gpu_info['type'] = 'rocm'
                self.logger.info("检测到AMD GPU (ROCm)")
                return gpu_info
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        try:
            # 检查Metal (Apple Silicon)
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

        self.logger.info("未检测到可用的GPU，将使用CPU")
        return gpu_info

    def _load_model(self) -> bool:
        """加载 AI 模型"""
        if not self.enabled:
            return False

        model_path = Path(self.config.ai.model_path).expanduser()

        # 检查模型文件是否存在
        if not model_path.exists():
            self.logger.warning(f"AI 模型文件不存在: {model_path}")

            # 可选：尝试下载模型
            if self.config.ai.model_url:
                self.logger.info(f"尝试下载模型: {self.config.ai.model_url}")
                if self._download_model():
                    self.logger.info("模型下载成功")
                else:
                    self.logger.error("模型下载失败，禁用 AI 功能")
                    self.enabled = False
                    return False
            else:
                self.logger.error("模型文件不存在且无下载 URL，禁用 AI 功能")
                self.enabled = False
                return False

        try:
            # 动态导入 llama-cpp-python
            from llama_cpp import Llama

            self.logger.info(f"加载 AI 模型: {model_path}")

            # 检测GPU
            self.gpu_info = self._detect_gpu()

            # 构建模型参数
            model_params = {
                'model_path': str(model_path),
                'n_ctx': self.config.ai.context_size,
                'n_threads': 4,
                'n_batch': 512,
                'verbose': False,
            }

            # 如果有GPU，启用GPU加速
            if self.gpu_info['available']:
                model_params['n_gpu_layers'] = self.gpu_info['n_gpu_layers']
                self.logger.info(f"启用GPU加速 ({self.gpu_info['type']})")

                # 根据GPU类型设置特定参数
                if self.gpu_info['type'] == 'metal':
                    # Metal (Apple Silicon) 特定设置
                    model_params['n_threads'] = 1  # Metal使用单线程更高效
                elif self.gpu_info['type'] == 'cuda':
                    # CUDA特定设置
                    import os
                    # 设置CUDA设备（如果有多个GPU）
                    if self.gpu_info['device_count'] > 1:
                        os.environ['CUDA_VISIBLE_DEVICES'] = '0'
            else:
                self.logger.info("使用CPU进行推理")

            self.model = Llama(**model_params)

            self.model_loaded = True
            self.logger.info("AI 模型加载成功")
            return True

        except ImportError:
            self.logger.error("llama-cpp-python 未安装，禁用 AI 功能")
            self.enabled = False
            return False
        except Exception as e:
            self.logger.error(f"加载 AI 模型失败: {e}")
            self.enabled = False
            return False
    
    def _download_model(self) -> bool:
        """下载模型文件"""
        # 这里可以添加模型下载逻辑
        # 由于下载大文件可能需要较长时间，这里只记录警告
        self.logger.warning("模型下载功能未实现，请手动下载模型文件")
        return False
    
    def _init_prompt_templates(self) -> None:
        """初始化提示词模板"""
        # 查询分析提示词
        self.query_analysis_template = """你是一个文件搜索助手。请分析用户的自然语言查询，提取搜索关键词和过滤条件。

用户查询：{query}

请按以下格式输出 JSON：
{{
  "keywords": ["关键词1", "关键词2", ...],
  "filters": {{
    "extensions": ["扩展名1", "扩展名2", ...],
    "min_size": 最小字节数,
    "max_size": 最大字节数,
    "modified_after": "YYYY-MM-DD",
    "modified_before": "YYYY-MM-DD"
  }},
  "intent": "用户意图描述",
  "confidence": 0.95
}}

注意：
- keywords：从查询中提取的核心搜索词
- filters：根据查询推断的过滤条件，没有则为空对象
- intent：简短描述用户想找什么
- confidence：分析结果的置信度（0-1）

示例：
用户查询："帮我找一下上周修改的PDF文档"
输出：
{{
  "keywords": ["文档"],
  "filters": {{
    "extensions": [".pdf"],
    "modified_after": "2024-01-15"
  }},
  "intent": "查找上周修改的PDF文档",
  "confidence": 0.9
}}

现在请分析以下查询："""
        
        # 回答生成提示词（使用配置中的模板）
        self.answer_template = self.config.ai.prompt_template
        
        # 摘要生成提示词
        self.summary_template = """请为以下文件内容生成简洁的摘要：

文件信息：
{file_info}

文件内容：
{content}

请生成一段简洁的摘要（不超过100字），突出文件的主要内容和关键信息。"""

    def parse_natural_language(self, query: str) -> QueryAnalysis:
        """
        解析自然语言查询
        
        Args:
            query: 自然语言查询字符串
            
        Returns:
            查询分析结果
        """
        if not self.enabled or not self.model_loaded:
            # 回退到简单解析
            return self._simple_parse(query)
        
        try:
            # 构建完整提示词
            prompt = self.query_analysis_template.format(query=query)
            
            # 调用模型
            response = self.model.create_completion(
                prompt,
                max_tokens=300,
                temperature=0.1,
                stop=["\n\n", "```"],
                echo=False,
            )
            
            if response:
                text = response['choices'][0]['text'].strip()
                
                # 提取 JSON 部分
                json_match = re.search(r'\{.*\}', text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    try:
                        data = json.loads(json_str)
                        
                        # 验证数据格式
                        if not isinstance(data.get('keywords', []), list):
                            data['keywords'] = []
                        if not isinstance(data.get('filters', {}), dict):
                            data['filters'] = {}
                        
                        return QueryAnalysis(
                            keywords=data.get('keywords', []),
                            filters=data.get('filters', {}),
                            intent=data.get('intent', ''),
                            confidence=data.get('confidence', 0.5)
                        )
                    except json.JSONDecodeError as e:
                        self.logger.error(f"解析 AI 响应 JSON 失败: {e}")
                        self.logger.debug(f"原始响应: {text}")
            
            # 如果 AI 解析失败，回退到简单解析
            return self._simple_parse(query)
            
        except Exception as e:
            self.logger.error(f"AI 解析自然语言失败: {e}")
            return self._simple_parse(query)
    
    def _simple_parse(self, query: str) -> QueryAnalysis:
        """
        简单解析自然语言查询（回退方法）
        
        Args:
            query: 自然语言查询字符串
            
        Returns:
            查询分析结果
        """
        # 提取关键词（简单分词）
        keywords = re.findall(r'[\u4e00-\u9fff\w]{2,}', query)
        
        # 提取文件类型
        extensions = []
        if 'pdf' in query.lower() or 'PDF' in query:
            extensions.append('.pdf')
        if 'word' in query.lower() or 'doc' in query.lower():
            extensions.append('.docx')
        if 'excel' in query.lower() or 'xls' in query.lower():
            extensions.append('.xlsx')
        if '文本' in query or 'txt' in query.lower():
            extensions.append('.txt')
        
        # 提取时间相关
        filters = {}
        if extensions:
            filters['extensions'] = extensions
        
        if '上周' in query or '上星期' in query:
            # 简单处理：设置为7天前
            import datetime
            week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
            filters['modified_after'] = week_ago.strftime('%Y-%m-%d')
        elif '昨天' in query:
            import datetime
            yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
            filters['modified_after'] = yesterday.strftime('%Y-%m-%d')
        
        # 提取大小相关
        size_match = re.search(r'(\d+)\s*(MB|GB|KB|字节)', query)
        if size_match:
            size = int(size_match.group(1))
            unit = size_match.group(2)
            
            # 转换为字节
            if unit == 'GB':
                size_bytes = size * 1024 * 1024 * 1024
            elif unit == 'MB':
                size_bytes = size * 1024 * 1024
            elif unit == 'KB':
                size_bytes = size * 1024
            else:
                size_bytes = size
            
            if '大于' in query or '超过' in query:
                filters['min_size'] = size_bytes
            elif '小于' in query or '少于' in query:
                filters['max_size'] = size_bytes
        
        return QueryAnalysis(
            keywords=keywords,
            filters=filters,
            intent=f"搜索: {query}",
            confidence=0.6
        )
    
    def generate_answer(self, question: str, context_files: List[Dict[str, Any]]) -> str:
        """
        基于文件内容生成回答
        
        Args:
            question: 用户问题
            context_files: 相关文件列表
            
        Returns:
            AI 生成的回答
        """
        if not self.enabled or not self.model_loaded:
            return self._simple_answer(question, context_files)
        
        if not context_files:
            return "没有找到相关的文件内容来回答这个问题。"
        
        try:
            # 构建文件上下文
            file_context = ""
            for i, file in enumerate(context_files[:5], 1):  # 限制前5个文件
                file_info = f"文件 {i}: {file.get('filename', '未知')} (路径: {file.get('path', '未知')})"
                content_preview = file.get('content_preview', '')
                
                file_context += f"{file_info}\n"
                if content_preview:
                    file_context += f"内容预览:\n{content_preview}\n"
                file_context += "-" * 40 + "\n"
            
            # 构建完整提示词
            prompt = self.answer_template.format(
                file_context=file_context,
                question=question
            )
            
            # 调用模型
            start_time = time.time()
            response = self.model.create_completion(
                prompt,
                max_tokens=self.config.ai.max_tokens,
                temperature=self.config.ai.temperature,
                stop=["\n\n", "文件：", "###"],
                echo=False,
            )
            elapsed = time.time() - start_time
            
            if response:
                answer = response['choices'][0]['text'].strip()
                self.logger.debug(f"AI 生成回答耗时: {elapsed:.2f}秒")
                
                # 清理回答
                answer = re.sub(r'^\s*(回答|Answer):\s*', '', answer)
                answer = re.sub(r'\n{3,}', '\n\n', answer)
                
                return answer
            else:
                return self._simple_answer(question, context_files)
                
        except Exception as e:
            self.logger.error(f"AI 生成回答失败: {e}")
            return self._simple_answer(question, context_files)
    
    def _simple_answer(self, question: str, context_files: List[Dict[str, Any]]) -> str:
        """简单回答生成（回退方法）"""
        if not context_files:
            return "没有找到相关的文件。"
        
        file_count = len(context_files)
        file_list = []
        
        for i, file in enumerate(context_files[:10], 1):
            filename = file.get('filename', '未知文件')
            path = file.get('path', '')
            size_mb = file.get('size', 0) / (1024 * 1024)
            
            file_list.append(f"{i}. {filename} ({size_mb:.1f} MB)")
            if 'highlights' in file and file['highlights']:
                file_list.append(f"   相关片段: {file['highlights']}")
        
        return f"找到 {file_count} 个相关文件：\n\n" + "\n".join(file_list)
    
    def summarize_file(self, file_content: str, file_info: str = "") -> str:
        """
        生成文件摘要
        
        Args:
            file_content: 文件内容
            file_info: 文件信息（可选）
            
        Returns:
            文件摘要
        """
        if not self.enabled or not self.model_loaded:
            return self._simple_summary(file_content)
        
        try:
            # 限制内容长度
            max_content_length = 3000
            if len(file_content) > max_content_length:
                file_content = file_content[:max_content_length] + "..."
            
            prompt = self.summary_template.format(
                file_info=file_info,
                content=file_content
            )
            
            response = self.model.create_completion(
                prompt,
                max_tokens=200,
                temperature=0.2,
                stop=["\n\n", "###"],
                echo=False,
            )
            
            if response:
                summary = response['choices'][0]['text'].strip()
                summary = re.sub(r'^\s*(摘要|Summary):\s*', '', summary)
                return summary
            else:
                return self._simple_summary(file_content)
                
        except Exception as e:
            self.logger.error(f"生成文件摘要失败: {e}")
            return self._simple_summary(file_content)
    
    def _simple_summary(self, file_content: str) -> str:
        """简单摘要生成（回退方法）"""
        # 提取前3行或前200字符
        lines = file_content.split('\n')
        preview_lines = []
        total_chars = 0
        
        for line in lines[:5]:  # 最多5行
            if total_chars + len(line) > 200:
                break
            preview_lines.append(line)
            total_chars += len(line)
        
        summary = ' '.join(preview_lines)
        if len(summary) > 200:
            summary = summary[:197] + '...'
        
        return summary
    
    def is_enabled(self) -> bool:
        """检查 AI 功能是否启用"""
        return self.enabled and self.model_loaded
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        if not self.enabled or not self.model_loaded:
            return {'enabled': False}

        model_path = Path(self.config.ai.model_path)

        return {
            'enabled': True,
            'model_path': str(model_path),
            'model_exists': model_path.exists(),
            'model_size_mb': model_path.stat().st_size / (1024 * 1024) if model_path.exists() else 0,
            'context_size': self.config.ai.context_size,
            'loaded': self.model_loaded,
            'gpu_available': self.gpu_info['available'] if self.gpu_info else False,
            'gpu_type': self.gpu_info['type'] if self.gpu_info else None,
        }
    
    def close(self) -> None:
        """关闭 AI 引擎"""
        if self.executor:
            self.executor.shutdown(wait=True)
        self.model = None
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


if __name__ == "__main__":
    # 测试 AI 引擎
    config = get_config()
    ai_engine = AIEngine(config)
    
    print(f"AI 引擎启用: {ai_engine.is_enabled()}")
    print(f"模型信息: {ai_engine.get_model_info()}")
    
    if ai_engine.is_enabled():
        # 测试自然语言解析
        query = "帮我找一下上周修改的PDF文档"
        analysis = ai_engine.parse_natural_language(query)
        print(f"\n查询分析: {query}")
        print(f"关键词: {analysis.keywords}")
        print(f"过滤条件: {analysis.filters}")
        print(f"意图: {analysis.intent}")
        print(f"置信度: {analysis.confidence}")
        
        # 测试回答生成
        context_files = [
            {
                'filename': 'test.pdf',
                'path': '/tmp/test.pdf',
                'size': 1024 * 1024,
                'content_preview': '这是一个测试PDF文件，包含一些示例内容。',
            }
        ]
        
        answer = ai_engine.generate_answer("这个文件讲的是什么？", context_files)
        print(f"\nAI 回答:\n{answer}")
    
    ai_engine.close()