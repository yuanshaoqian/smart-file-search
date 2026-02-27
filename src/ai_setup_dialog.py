#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 设置向导对话框
帮助用户轻松配置 AI 功能
"""

import webbrowser
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QTextEdit, QComboBox, QCheckBox, QMessageBox,
    QProgressBar, QWidget, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon, QColor

from loguru import logger


class OllamaInstallThread(QThread):
    """Ollama 安装检测线程"""
    finished = pyqtSignal(bool, str)  # success, message

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        import subprocess
        import shutil

        try:
            # 检查是否已安装
            if shutil.which('ollama'):
                self.finished.emit(True, "Ollama 已安装")
                return

            # 尝试自动安装（仅限支持的系统）
            import platform
            system = platform.system()

            if system == "Darwin":  # macOS
                # 检查是否有 brew
                if shutil.which('brew'):
                    result = subprocess.run(
                        ['brew', 'install', 'ollama'],
                        capture_output=True, text=True, timeout=300
                    )
                    if result.returncode == 0:
                        self.finished.emit(True, "Ollama 安装成功！")
                        return

            # 需要手动安装
            self.finished.emit(False, "请手动安装 Ollama")

        except Exception as e:
            self.finished.emit(False, f"检测失败: {str(e)}")


class AISetupDialog(QDialog):
    """AI 设置向导对话框"""

    def __init__(self, ai_engine, config, parent=None):
        super().__init__(parent)
        self.ai_engine = ai_engine
        self.config = config
        self.logger = logger.bind(module="ai_setup")

        self.setWindowTitle("AI 功能设置")
        self.setMinimumSize(600, 500)
        self.resize(650, 550)

        self._setup_ui()
        self._refresh_backends()

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # 标题
        title = QLabel("AI 智能搜索配置")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # 当前状态
        status_group = QGroupBox("当前状态")
        status_layout = QVBoxLayout(status_group)

        self.status_label = QLabel("正在检测...")
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)

        layout.addWidget(status_group)

        # 后端选择
        backend_group = QGroupBox("AI 后端选择")
        backend_layout = QVBoxLayout(backend_group)

        self.backend_combo = QComboBox()
        self.backend_combo.currentIndexChanged.connect(self._on_backend_changed)
        backend_layout.addWidget(self.backend_combo)

        self.backend_desc = QLabel("")
        self.backend_desc.setWordWrap(True)
        self.backend_desc.setStyleSheet("color: #888; font-size: 11px;")
        backend_layout.addWidget(self.backend_desc)

        layout.addWidget(backend_group)

        # 安装指南
        install_group = QGroupBox("安装指南")
        install_layout = QVBoxLayout(install_group)

        self.install_text = QTextEdit()
        self.install_text.setReadOnly(True)
        self.install_text.setMaximumHeight(150)
        self.install_text.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 10px;
                font-family: Consolas, 'Courier New', monospace;
            }
        """)
        install_layout.addWidget(self.install_text)

        # 按钮行
        btn_layout = QHBoxLayout()

        self.website_btn = QPushButton("打开官网")
        self.website_btn.clicked.connect(self._open_website)
        btn_layout.addWidget(self.website_btn)

        self.install_btn = QPushButton("复制安装命令")
        self.install_btn.clicked.connect(self._copy_install_command)
        btn_layout.addWidget(self.install_btn)

        self.refresh_btn = QPushButton("刷新状态")
        self.refresh_btn.clicked.connect(self._refresh_backends)
        btn_layout.addWidget(self.refresh_btn)

        install_layout.addLayout(btn_layout)
        layout.addWidget(install_group)

        # AI 功能选项
        options_group = QGroupBox("AI 功能选项")
        options_layout = QVBoxLayout(options_group)

        self.enable_ai_checkbox = QCheckBox("启用 AI 智能搜索")
        self.enable_ai_checkbox.setChecked(self.config.ai.enabled)
        options_layout.addWidget(self.enable_ai_checkbox)

        hint_label = QLabel("提示：即使不安装AI模型，智能匹配模式也能提供增强的搜索体验")
        hint_label.setStyleSheet("color: #888; font-size: 10px;")
        hint_label.setWordWrap(True)
        options_layout.addWidget(hint_label)

        layout.addWidget(options_group)

        # 底部按钮
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()

        self.save_btn = QPushButton("保存设置")
        self.save_btn.clicked.connect(self._save_settings)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                border: none;
                border-radius: 5px;
                padding: 10px 30px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1e8ae6;
            }
        """)
        bottom_layout.addWidget(self.save_btn)

        self.close_btn = QPushButton("取消")
        self.close_btn.clicked.connect(self.reject)
        bottom_layout.addWidget(self.close_btn)

        layout.addLayout(bottom_layout)

        # 应用样式
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QGroupBox {
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLabel {
                color: #ffffff;
            }
            QComboBox {
                background-color: #3c3c3c;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 8px;
                color: white;
                min-width: 200px;
            }
            QComboBox:hover {
                border: 1px solid #0078d4;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #3c3c3c;
                color: white;
                selection-background-color: #0078d4;
            }
            QCheckBox {
                color: white;
            }
            QPushButton {
                background-color: #3c3c3c;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 8px 16px;
                color: white;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
        """)

    def _refresh_backends(self):
        """刷新可用后端列表"""
        self.status_label.setText("正在检测 AI 后端...")

        backends = self.ai_engine.get_available_backends()

        self.backend_combo.clear()
        self._backend_data = []

        for backend in backends:
            status = "✓ " if backend['available'] else "✗ "
            self.backend_combo.addItem(f"{status}{backend['name']}")
            self._backend_data.append(backend)

        # 更新状态
        current_backend = self.ai_engine.backend_type
        for i, backend in enumerate(backends):
            if backend['id'] == current_backend:
                self.backend_combo.setCurrentIndex(i)
                break

        # 更新状态标签
        info = self.ai_engine.get_model_info()
        status_text = f"当前后端: {info['backend']}\n"
        if info['backend'] == 'simple':
            status_text += "状态: 使用智能匹配模式（无需AI模型）"
        elif info.get('model_loaded'):
            status_text += "状态: AI 模型已加载"
        elif info['backend'] == 'ollama':
            backend_status = info.get('backend_status', {})
            if backend_status.get('available'):
                status_text += "状态: Ollama 服务运行中"
            else:
                status_text += "状态: Ollama 已安装但未运行"
        else:
            status_text += "状态: 未配置"

        self.status_label.setText(status_text)

        self._on_backend_changed(self.backend_combo.currentIndex())

    def _on_backend_changed(self, index):
        """后端选择改变"""
        if index < 0 or index >= len(self._backend_data):
            return

        backend = self._backend_data[index]

        # 更新描述
        self.backend_desc.setText(backend['description'])

        # 更新安装指南
        install_text = f"=== {backend['name']} ===\n\n"
        install_text += f"状态: {'可用' if backend['available'] else '不可用'}\n\n"

        if backend['install_command']:
            install_text += f"安装命令:\n{backend['install_command']}\n\n"

        if backend['id'] == 'ollama':
            install_text += """安装步骤：
1. 访问 https://ollama.ai 下载安装
2. 安装后运行: ollama pull llama3.2:1b
3. Ollama 会自动在后台运行

推荐模型:
- llama3.2:1b (约1GB，推荐)
- qwen2.5:1.5b (约1.5GB，中文友好)
- gemma2:2b (约2GB)"""
        elif backend['id'] == 'llama-cpp-python':
            install_text += """安装命令:
pip install llama-cpp-python

GPU加速版本:
# CUDA
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python

# Metal (macOS)
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python

需要下载GGUF模型文件到 data/models/ 目录"""
        elif backend['id'] == 'simple':
            install_text += """智能匹配模式是内置功能，无需安装任何依赖。

功能包括：
- 自动识别文件类型关键词（PDF、Word、Excel等）
- 时间范围识别（今天、昨天、本周等）
- 文件大小识别（大文件、小文件等）
- 智能关键词提取

这是最简单的使用方式，虽然不是真正的AI，但能提供不错的搜索体验。"""

        self.install_text.setText(install_text)

        # 更新按钮状态
        self.website_btn.setEnabled(backend['website'] is not None)
        self.install_btn.setEnabled(backend['install_command'] is not None)

    def _open_website(self):
        """打开官网"""
        index = self.backend_combo.currentIndex()
        if index >= 0 and index < len(self._backend_data):
            website = self._backend_data[index].get('website')
            if website:
                webbrowser.open(website)

    def _copy_install_command(self):
        """复制安装命令"""
        index = self.backend_combo.currentIndex()
        if index >= 0 and index < len(self._backend_data):
            command = self._backend_data[index].get('install_command')
            if command:
                from PyQt6.QtWidgets import QApplication
                QApplication.clipboard().setText(command)
                QMessageBox.information(self, "已复制", f"安装命令已复制到剪贴板:\n\n{command}")

    def _save_settings(self):
        """保存设置"""
        try:
            # 更新配置
            self.config.ai.enabled = self.enable_ai_checkbox.isChecked()

            # 保存配置文件
            from .config import save_config
            save_config(self.config)

            QMessageBox.information(
                self,
                "设置已保存",
                "AI 设置已保存。部分设置可能需要重启应用才能生效。"
            )

            self.accept()

        except Exception as e:
            self.logger.error(f"保存设置失败: {e}")
            QMessageBox.critical(self, "错误", f"保存设置失败: {str(e)}")
