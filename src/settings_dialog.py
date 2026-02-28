#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置对话框
提供图形化的配置界面
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox,
    QPushButton, QGroupBox, QFormLayout, QComboBox, QTextEdit,
    QListWidget, QListWidgetItem, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from loguru import logger
from pathlib import Path
from typing import Optional

try:
    from src.config import get_config, save_config, AppConfig
except ImportError:
    from config import get_config, save_config, AppConfig


class SettingsDialog(QDialog):
    """设置对话框"""
    
    # 配置已更改信号
    config_changed = pyqtSignal()
    
    def __init__(self, config: Optional[AppConfig] = None, parent=None):
        super().__init__(parent)
        
        self.config = config or get_config()
        self.logger = logger.bind(module="settings")
        
        self.setWindowTitle("设置")
        self.setMinimumSize(600, 500)
        self.resize(700, 600)
        
        self._init_ui()
        self._load_settings()
    
    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 标签页
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # 添加各个设置页
        self.tabs.addTab(self._create_general_tab(), "常规")
        self.tabs.addTab(self._create_index_tab(), "索引")
        self.tabs.addTab(self._create_ai_tab(), "AI")
        self.tabs.addTab(self._create_gui_tab(), "界面")
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.ok_btn = QPushButton("确定")
        self.ok_btn.clicked.connect(self._on_ok)
        button_layout.addWidget(self.ok_btn)
        
        self.apply_btn = QPushButton("应用")
        self.apply_btn.clicked.connect(self._on_apply)
        button_layout.addWidget(self.apply_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _create_general_tab(self) -> QWidget:
        """创建常规设置页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 语言设置
        lang_group = QGroupBox("语言")
        lang_layout = QFormLayout()
        
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("简体中文", "zh_CN")
        self.lang_combo.addItem("English", "en_US")
        lang_layout.addRow("界面语言:", self.lang_combo)
        
        lang_group.setLayout(lang_layout)
        layout.addWidget(lang_group)
        
        # 更新设置
        update_group = QGroupBox("更新")
        update_layout = QFormLayout()
        
        self.auto_update_check = QCheckBox("自动检查更新")
        update_layout.addRow(self.auto_update_check)
        
        update_group.setLayout(update_layout)
        layout.addWidget(update_group)
        
        layout.addStretch()
        return widget
    
    def _create_index_tab(self) -> QWidget:
        """创建索引设置页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 索引目录
        dir_group = QGroupBox("索引目录")
        dir_layout = QVBoxLayout()
        
        self.dir_list = QListWidget()
        self.dir_list.setMaximumHeight(150)
        dir_layout.addWidget(self.dir_list)
        
        dir_btn_layout = QHBoxLayout()
        
        self.add_dir_btn = QPushButton("添加目录")
        self.add_dir_btn.clicked.connect(self._add_index_dir)
        dir_btn_layout.addWidget(self.add_dir_btn)
        
        self.remove_dir_btn = QPushButton("移除目录")
        self.remove_dir_btn.clicked.connect(self._remove_index_dir)
        dir_btn_layout.addWidget(self.remove_dir_btn)
        
        dir_btn_layout.addStretch()
        dir_layout.addLayout(dir_btn_layout)
        
        dir_group.setLayout(dir_layout)
        layout.addWidget(dir_group)
        
        # 文件过滤
        filter_group = QGroupBox("文件过滤")
        filter_layout = QFormLayout()

        # 过滤模式选择
        self.filter_mode_combo = QComboBox()
        self.filter_mode_combo.addItem("排除模式 - 排除匹配的文件", "exclude")
        self.filter_mode_combo.addItem("包含模式 - 只索引匹配的文件", "include")
        self.filter_mode_combo.currentIndexChanged.connect(self._on_filter_mode_changed)
        filter_layout.addRow("过滤模式:", self.filter_mode_combo)

        self.exclude_patterns = QTextEdit()
        self.exclude_patterns.setMaximumHeight(80)
        self.exclude_patterns.setPlaceholderText("每行一个排除模式，例如：\n*.tmp\n*.log\n.git")
        filter_layout.addRow("排除模式:", self.exclude_patterns)

        self.include_patterns = QTextEdit()
        self.include_patterns.setMaximumHeight(80)
        self.include_patterns.setPlaceholderText("每行一个包含模式，例如：\n*.py\n*.md\nsrc/")
        filter_layout.addRow("包含模式:", self.include_patterns)

        self.max_file_size = QSpinBox()
        self.max_file_size.setRange(1, 1000)
        self.max_file_size.setSuffix(" MB")
        filter_layout.addRow("最大文件大小:", self.max_file_size)

        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # 索引更新
        update_group = QGroupBox("索引更新")
        update_layout = QFormLayout()
        
        self.update_interval = QSpinBox()
        self.update_interval.setRange(0, 3600)
        self.update_interval.setSuffix(" 秒")
        update_layout.addRow("更新间隔 (0=禁用):", self.update_interval)
        
        self.incremental_check = QCheckBox("增量更新")
        update_layout.addRow(self.incremental_check)
        
        update_group.setLayout(update_layout)
        layout.addWidget(update_group)
        
        layout.addStretch()
        return widget
    
    def _create_ai_tab(self) -> QWidget:
        """创建 AI 设置页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # AI 启用
        enable_group = QGroupBox("AI 功能")
        enable_layout = QVBoxLayout()
        
        self.ai_enabled = QCheckBox("启用 AI 功能")
        self.ai_enabled.toggled.connect(self._on_ai_enabled_changed)
        enable_layout.addWidget(self.ai_enabled)
        
        enable_group.setLayout(enable_layout)
        layout.addWidget(enable_group)
        
        # 模型设置
        model_group = QGroupBox("模型设置")
        model_layout = QFormLayout()
        
        self.model_path = QLineEdit()
        model_layout.addRow("模型路径:", self.model_path)
        
        model_btn_layout = QHBoxLayout()
        self.browse_model_btn = QPushButton("浏览...")
        self.browse_model_btn.clicked.connect(self._browse_model)
        model_btn_layout.addWidget(self.browse_model_btn)
        model_btn_layout.addStretch()
        model_layout.addRow("", model_btn_layout)
        
        self.context_size = QSpinBox()
        self.context_size.setRange(256, 8192)
        self.context_size.setSuffix(" tokens")
        model_layout.addRow("上下文长度:", self.context_size)
        
        self.max_tokens = QSpinBox()
        self.max_tokens.setRange(64, 2048)
        self.max_tokens.setSuffix(" tokens")
        model_layout.addRow("最大生成长度:", self.max_tokens)
        
        self.temperature = QDoubleSpinBox()
        self.temperature.setRange(0.0, 2.0)
        self.temperature.setSingleStep(0.1)
        model_layout.addRow("温度:", self.temperature)
        
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        # 说明
        info_label = QLabel(
            "💡 提示：\n"
            "• AI 模型需要单独下载（约 1.7GB）\n"
            "• 首次使用 AI 功能时会提示下载\n"
            "• 低配置电脑建议降低上下文长度"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; padding: 10px;")
        layout.addWidget(info_label)
        
        layout.addStretch()
        return widget
    
    def _create_gui_tab(self) -> QWidget:
        """创建界面设置页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 主题
        theme_group = QGroupBox("主题")
        theme_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("深色", "dark")
        self.theme_combo.addItem("浅色", "light")
        self.theme_combo.addItem("跟随系统", "system")
        theme_layout.addRow("主题:", self.theme_combo)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # 显示设置
        display_group = QGroupBox("显示")
        display_layout = QFormLayout()
        
        self.max_results = QSpinBox()
        self.max_results.setRange(50, 1000)
        display_layout.addRow("最大结果数:", self.max_results)
        
        self.preview_lines = QSpinBox()
        self.preview_lines.setRange(5, 50)
        display_layout.addRow("预览行数:", self.preview_lines)
        
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)
        
        layout.addStretch()
        return widget
    
    def _load_settings(self):
        """加载当前设置"""
        # 常规
        lang_index = self.lang_combo.findData(self.config.language)
        if lang_index >= 0:
            self.lang_combo.setCurrentIndex(lang_index)

        self.auto_update_check.setChecked(self.config.update_check.enabled)

        # 索引
        self.dir_list.clear()
        for dir_path in self.config.index.directories:
            self.dir_list.addItem(dir_path)

        # 过滤模式
        filter_mode = getattr(self.config.index, 'filter_mode', 'exclude')
        filter_mode_index = self.filter_mode_combo.findData(filter_mode)
        if filter_mode_index >= 0:
            self.filter_mode_combo.setCurrentIndex(filter_mode_index)

        self.exclude_patterns.setText(
            '\n'.join(self.config.index.exclude_patterns)
        )

        # 包含模式
        include_patterns = getattr(self.config.index, 'include_patterns', [])
        self.include_patterns.setText('\n'.join(include_patterns))

        # 更新过滤模式的UI状态
        self._on_filter_mode_changed(self.filter_mode_combo.currentIndex())

        self.max_file_size.setValue(
            self.config.index.max_file_size // (1024 * 1024)
        )

        self.update_interval.setValue(self.config.index.update_interval)
        self.incremental_check.setChecked(self.config.index.incremental)
        
        # AI
        self.ai_enabled.setChecked(self.config.ai.enabled)
        self.model_path.setText(self.config.ai.model_path)
        self.context_size.setValue(self.config.ai.context_size)
        self.max_tokens.setValue(self.config.ai.max_tokens)
        self.temperature.setValue(self.config.ai.temperature)
        
        # 界面
        theme_index = self.theme_combo.findData(self.config.gui.theme)
        if theme_index >= 0:
            self.theme_combo.setCurrentIndex(theme_index)
        
        self.max_results.setValue(self.config.gui.max_results)
        self.preview_lines.setValue(self.config.gui.preview_max_lines)
        
        # 更新 AI 控件状态
        self._on_ai_enabled_changed(self.config.ai.enabled)
    
    def _save_settings(self):
        """保存设置"""
        # 显示保存状态
        self.ok_btn.setEnabled(False)
        self.apply_btn.setEnabled(False)
        self.ok_btn.setText("保存中...")

        # 强制处理事件，确保UI更新
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        try:
            # 常规
            self.config.language = self.lang_combo.currentData()
            self.config.update_check.enabled = self.auto_update_check.isChecked()

            # 索引
            self.config.index.directories = [
                self.dir_list.item(i).text()
                for i in range(self.dir_list.count())
            ]

            # 过滤模式
            self.config.index.filter_mode = self.filter_mode_combo.currentData()

            self.config.index.exclude_patterns = [
                line.strip()
                for line in self.exclude_patterns.toPlainText().split('\n')
                if line.strip()
            ]

            self.config.index.include_patterns = [
                line.strip()
                for line in self.include_patterns.toPlainText().split('\n')
                if line.strip()
            ]

            self.config.index.max_file_size = self.max_file_size.value() * 1024 * 1024
            self.config.index.update_interval = self.update_interval.value()
            self.config.index.incremental = self.incremental_check.isChecked()

            # AI
            self.config.ai.enabled = self.ai_enabled.isChecked()
            self.config.ai.model_path = self.model_path.text()
            self.config.ai.context_size = self.context_size.value()
            self.config.ai.max_tokens = self.max_tokens.value()
            self.config.ai.temperature = self.temperature.value()

            # 验证AI配置
            if self.config.ai.enabled:
                model_path = Path(self.config.ai.model_path).expanduser()
                if not model_path.exists():
                    reply = QMessageBox.question(
                        self,
                        "AI 模型文件不存在",
                        f"AI 模型文件不存在：\n{model_path}\n\n"
                        "AI 功能需要模型文件才能正常工作。\n"
                        "是否禁用 AI 功能？",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.Yes
                    )
                    if reply == QMessageBox.StandardButton.Yes:
                        self.config.ai.enabled = False
                    else:
                        QMessageBox.information(
                            self,
                            "提示",
                            "您可以从以下地址下载模型文件：\n"
                            "https://huggingface.co/TheBloke/phi-2-GGUF\n\n"
                            "下载后将文件放在配置的路径，然后重新启用 AI 功能。"
                        )
                        return False

            # 界面
            self.config.gui.theme = self.theme_combo.currentData()
            self.config.gui.max_results = self.max_results.value()
            self.config.gui.preview_max_lines = self.preview_lines.value()

            # 验证配置
            if not self.config.index.directories:
                QMessageBox.warning(self, "配置错误", "请至少添加一个索引目录！")
                return False

            # 保存到文件
            save_config(self.config)

            self.logger.info("设置已保存")
            return True

        except Exception as e:
            self.logger.error(f"保存设置失败: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, "保存失败", f"保存设置时出错：\n{str(e)}\n\n请查看日志获取详细信息。")
            return False

        finally:
            # 恢复按钮状态
            self.ok_btn.setEnabled(True)
            self.apply_btn.setEnabled(True)
            self.ok_btn.setText("确定")
            QApplication.processEvents()
    
    def _add_index_dir(self):
        """添加索引目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择索引目录",
            str(Path.home())
        )
        
        if dir_path:
            # 检查是否已存在
            for i in range(self.dir_list.count()):
                if self.dir_list.item(i).text() == dir_path:
                    QMessageBox.information(self, "提示", "该目录已存在")
                    return
            
            self.dir_list.addItem(dir_path)
    
    def _remove_index_dir(self):
        """移除索引目录"""
        current_item = self.dir_list.currentItem()
        if current_item:
            self.dir_list.takeItem(self.dir_list.row(current_item))
    
    def _browse_model(self):
        """浏览模型文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择模型文件",
            str(Path(self.model_path.text()).parent),
            "GGUF 模型 (*.gguf);;所有文件 (*.*)"
        )
        
        if file_path:
            self.model_path.setText(file_path)
    
    def _on_filter_mode_changed(self, index: int):
        """过滤模式改变"""
        mode = self.filter_mode_combo.currentData()
        if mode == "exclude":
            # 排除模式：启用排除模式输入，禁用包含模式输入
            self.exclude_patterns.setEnabled(True)
            self.include_patterns.setEnabled(False)
            self.exclude_patterns.setStyleSheet("")
            self.include_patterns.setStyleSheet("color: #666; background-color: #3a3a3a;")
        else:
            # 包含模式：禁用排除模式输入，启用包含模式输入
            self.exclude_patterns.setEnabled(False)
            self.include_patterns.setEnabled(True)
            self.exclude_patterns.setStyleSheet("color: #666; background-color: #3a3a3a;")
            self.include_patterns.setStyleSheet("")

    def _on_ai_enabled_changed(self, enabled: bool):
        """AI 启用状态改变"""
        self.model_path.setEnabled(enabled)
        self.browse_model_btn.setEnabled(enabled)
        self.context_size.setEnabled(enabled)
        self.max_tokens.setEnabled(enabled)
        self.temperature.setEnabled(enabled)
    
    def _on_ok(self):
        """确定按钮"""
        if self._save_settings():
            self.config_changed.emit()
            self.accept()
    
    def _on_apply(self):
        """应用按钮"""
        if self._save_settings():
            self.config_changed.emit()
            QMessageBox.information(self, "成功", "设置已保存并生效")
