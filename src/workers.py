#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作线程模块
将耗时操作放在后台线程，避免界面卡顿
"""

from PyQt6.QtCore import QThread, pyqtSignal
from loguru import logger
from typing import List, Dict, Any, Optional
from pathlib import Path


class IndexWorker(QThread):
    """索引工作线程"""
    
    # 信号
    progress = pyqtSignal(str, int, int)  # 消息, 当前进度, 总数
    finished = pyqtSignal(int)  # 索引文件数
    error = pyqtSignal(str)  # 错误消息
    
    def __init__(self, index_manager, directories, parent=None):
        super().__init__(parent)
        self.index_manager = index_manager
        self.directories = directories
        self._is_cancelled = False
        
    def run(self):
        """执行索引"""
        try:
            total_files = 0
            
            for directory in self.directories:
                if self._is_cancelled:
                    break
                    
                self.progress.emit(f"正在索引: {directory}", 0, 0)
                
                # 调用索引管理器
                count = self.index_manager.index_directory(
                    directory,
                    callback=lambda msg, cur, total: self.progress.emit(msg, cur, total)
                )
                
                total_files += count
                
            self.finished.emit(total_files)
            
        except Exception as e:
            self.error.emit(str(e))
            logger.error(f"索引失败: {e}")
            
    def cancel(self):
        """取消索引"""
        self._is_cancelled = True


class SearchWorker(QThread):
    """搜索工作线程"""
    
    # 信号
    results_ready = pyqtSignal(list)  # 搜索结果
    error = pyqtSignal(str)  # 错误消息
    
    def __init__(self, search_engine, query, parent=None):
        super().__init__(parent)
        self.search_engine = search_engine
        self.query = query
        
    def run(self):
        """执行搜索"""
        try:
            results = self.search_engine.search(self.query)
            self.results_ready.emit(results)
        except Exception as e:
            self.error.emit(str(e))
            logger.error(f"搜索失败: {e}")


class AIWorker(QThread):
    """AI工作线程"""
    
    # 信号
    response_ready = pyqtSignal(str)  # AI回答
    error = pyqtSignal(str)  # 错误消息
    
    def __init__(self, ai_engine, question, file_context, parent=None):
        super().__init__(parent)
        self.ai_engine = ai_engine
        self.question = question
        self.file_context = file_context
        
    def run(self):
        """执行AI推理"""
        try:
            response = self.ai_engine.answer_question(
                self.question,
                self.file_context
            )
            self.response_ready.emit(response)
        except Exception as e:
            self.error.emit(str(e))
            logger.error(f"AI推理失败: {e}")


class ModelDownloadWorker(QThread):
    """模型下载工作线程"""
    
    # 信号
    progress = pyqtSignal(str, int, int)  # 消息, 已下载, 总大小
    finished = pyqtSignal(str)  # 完成消息
    error = pyqtSignal(str)  # 错误消息
    
    def __init__(self, model_url, model_path, parent=None):
        super().__init__(parent)
        self.model_url = model_url
        self.model_path = Path(model_path)
        
    def run(self):
        """下载模型"""
        try:
            import urllib.request
            
            self.progress.emit("正在连接服务器...", 0, 0)
            
            # 创建目录
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 下载文件
            def progress_callback(count, block_size, total_size):
                downloaded = count * block_size
                mb_downloaded = downloaded // (1024 * 1024)
                mb_total = total_size // (1024 * 1024)
                self.progress.emit(
                    f"正在下载模型... {mb_downloaded}MB / {mb_total}MB",
                    downloaded,
                    total_size
                )
            
            urllib.request.urlretrieve(
                self.model_url,
                str(self.model_path),
                reporthook=progress_callback
            )
            
            self.finished.emit(f"模型下载完成: {self.model_path}")
            
        except Exception as e:
            self.error.emit(f"下载失败: {str(e)}")
            logger.error(f"模型下载失败: {e}")
