#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图形界面模块
基于 PyQt6 的现代化桌面应用界面
"""

import sys
import os
import time
import webbrowser
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTextEdit, QTableWidget, QTableWidgetItem,
    QLabel, QSplitter, QGroupBox, QComboBox, QSpinBox, QCheckBox,
    QStatusBar, QMenuBar, QMenu, QToolBar, QFileDialog, QMessageBox,
    QProgressDialog, QAbstractItemView, QHeaderView, QFrame,
    QListWidget, QListWidgetItem, QDateEdit, QTabWidget, QPlainTextEdit,
    QStyle, QSizePolicy, QDialog, QProgressBar
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QSize, QDate, QSettings,
    QRegularExpression
)
from PyQt6.QtGui import (
    QFont, QIcon, QColor, QPalette, QAction, QKeySequence,
    QDesktopServices, QShortcut
)
from loguru import logger

from .config import get_config


class IndexProgressDialog(QDialog):
    """索引进度对话框 - 显示详细的索引进度信息"""

    # 取消信号
    cancelled = pyqtSignal()

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumSize(500, 200)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint
        )
        self._setup_ui()
        self._was_cancelled = False

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # 主状态标签
        self.status_label = QLabel("准备开始...")
        self.status_label.setFont(QFont("Microsoft YaHei", 11))
        layout.addWidget(self.status_label)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% (%v / %m)")
        layout.addWidget(self.progress_bar)

        # 详细信息标签
        self.detail_label = QLabel("")
        self.detail_label.setFont(QFont("Microsoft YaHei", 9))
        self.detail_label.setWordWrap(True)
        self.detail_label.setStyleSheet("color: #888;")
        layout.addWidget(self.detail_label)

        # 统计信息
        stats_layout = QHBoxLayout()
        self.indexed_label = QLabel("已索引: 0")
        self.skipped_label = QLabel("跳过: 0")
        self.failed_label = QLabel("失败: 0")
        for label in [self.indexed_label, self.skipped_label, self.failed_label]:
            label.setFont(QFont("Microsoft YaHei", 9))
            stats_layout.addWidget(label)
        layout.addLayout(stats_layout)

        layout.addStretch()

        # 取消按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setMinimumWidth(100)
        self.cancel_btn.clicked.connect(self.cancel)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        # 应用样式
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QProgressBar {
                border: 2px solid #555;
                border-radius: 5px;
                text-align: center;
                background-color: #3c3c3c;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #0078d4;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1e8ae6;
            }
            QPushButton:pressed {
                background-color: #006cbd;
            }
        """)

    def update_progress(self, current: int, total: int, filename: str = "", status: str = ""):
        """更新进度"""
        # 更新进度条
        if total > 0:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
        else:
            self.progress_bar.setRange(0, 0)  # 不确定进度模式

        # 更新状态文本
        if status:
            self.status_label.setText(status)

        # 更新详细信息
        if filename:
            # 显示文件名（最多显示60个字符）
            display_name = Path(filename).name
            if len(display_name) > 60:
                display_name = display_name[:57] + "..."
            self.detail_label.setText(f"当前文件: {display_name}")
        else:
            self.detail_label.setText("")

        # 强制刷新界面
        QApplication.processEvents()

    def update_stats(self, indexed: int, skipped: int, failed: int):
        """更新统计信息"""
        self.indexed_label.setText(f"已索引: {indexed}")
        self.skipped_label.setText(f"跳过: {skipped}")
        self.failed_label.setText(f"失败: {failed}")

    def cancel(self):
        """取消操作"""
        if self._was_cancelled:
            return
        self._was_cancelled = True
        self.status_label.setText("正在取消...")
        self.cancel_btn.setEnabled(False)
        self.cancelled.emit()

    def was_cancelled(self) -> bool:
        """检查是否被取消"""
        return self._was_cancelled

    def close_with_cancel(self):
        """取消并关闭对话框"""
        self._was_cancelled = True
        self.reject()


class WorkerThread(QThread):
    """后台工作线程"""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, int, str, str)  # current, total, filename, status
    stats_update = pyqtSignal(int, int, int)  # indexed, skipped, failed

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class SearchThread(QThread):
    """搜索线程 - 避免UI假死"""
    finished = pyqtSignal(list, float)  # results, elapsed_time
    error = pyqtSignal(str)

    def __init__(self, indexer, query, limit, filters):
        super().__init__()
        self.indexer = indexer
        self.query = query
        self.limit = limit
        self.filters = filters

    def run(self):
        try:
            start_time = time.time()
            results = self.indexer.search(self.query, limit=self.limit, filters=self.filters)
            elapsed = time.time() - start_time
            self.finished.emit(results, elapsed)
        except Exception as e:
            self.error.emit(str(e))


class AISearchThread(QThread):
    """AI搜索线程 - 避免UI假死"""
    finished = pyqtSignal(object, list, float)  # analysis, results, elapsed_time
    error = pyqtSignal(str)

    def __init__(self, ai_engine, indexer, query, max_results, filters):
        super().__init__()
        self.ai_engine = ai_engine
        self.indexer = indexer
        self.query = query
        self.max_results = max_results
        self.filters = filters

    def run(self):
        try:
            import time
            start_time = time.time()

            # 使用 AI 解析自然语言
            analysis = self.ai_engine.parse_natural_language(self.query)

            # 构建搜索查询
            if analysis.keywords:
                search_query = " ".join(analysis.keywords)
            else:
                search_query = self.query

            # 合并过滤条件
            filters = self.filters.copy()
            if analysis.filters:
                filters.update(analysis.filters)

            # 执行搜索
            results = self.indexer.search(search_query, limit=self.max_results, filters=filters)

            elapsed = time.time() - start_time
            self.finished.emit(analysis, results, elapsed)
        except Exception as e:
            self.error.emit(str(e))


class SearchResultTable(QTableWidget):
    """搜索结果表格组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        # 设置列
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(['文件名', '路径', '大小', '修改时间', '匹配度'])
        
        # 设置选择行为
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        
        # 设置列宽
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        # 设置行高
        self.verticalHeader().setDefaultSectionSize(30)
        
        # 双击打开文件
        self.cellDoubleClicked.connect(self.on_double_click)
    
    def display_results(self, results: List[Dict[str, Any]]):
        """显示搜索结果"""
        self.setRowCount(len(results))
        
        for row, result in enumerate(results):
            # 文件名
            filename_item = QTableWidgetItem(result.get('filename', ''))
            filename_item.setData(Qt.ItemDataRole.UserRole, result)
            self.setItem(row, 0, filename_item)
            
            # 路径
            path = result.get('path', '')
            # 显示相对路径或截断路径
            display_path = path if len(path) <= 80 else '...' + path[-77:]
            path_item = QTableWidgetItem(display_path)
            path_item.setToolTip(path)
            self.setItem(row, 1, path_item)
            
            # 大小
            size = result.get('size', 0)
            size_str = self._format_size(size)
            size_item = QTableWidgetItem(size_str)
            size_item.setData(Qt.ItemDataRole.UserRole, size)  # 用于排序
            self.setItem(row, 2, size_item)
            
            # 修改时间
            modified = result.get('modified')
            if modified:
                if isinstance(modified, datetime):
                    time_str = modified.strftime('%Y-%m-%d %H:%M')
                else:
                    time_str = str(modified)
            else:
                time_str = '-'
            time_item = QTableWidgetItem(time_str)
            self.setItem(row, 3, time_item)
            
            # 匹配度
            score = result.get('score', 0)
            score_str = f"{score:.2f}" if score else "-"
            score_item = QTableWidgetItem(score_str)
            self.setItem(row, 4, score_item)
    
    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def on_double_click(self, row: int, column: int):
        """双击事件处理"""
        try:
            item = self.item(row, 0)
            if item:
                result = item.data(Qt.ItemDataRole.UserRole)
                if result:
                    path = result.get('path', '')
                    self.open_file(path)
        except Exception as e:
            from loguru import logger
            logger.error(f"双击打开文件失败: {e}")

    def open_file(self, path: str):
        """打开文件"""
        try:
            if path and Path(path).exists():
                QDesktopServices.openUrl(Path(path).as_uri())
            else:
                from loguru import logger
                logger.warning(f"文件不存在: {path}")
        except Exception as e:
            from loguru import logger
            logger.error(f"打开文件失败 {path}: {e}")
    
    def get_selected_file(self) -> Optional[Dict[str, Any]]:
        """获取选中的文件"""
        selected = self.selectedItems()
        if selected:
            row = selected[0].row()
            item = self.item(row, 0)
            if item:
                return item.data(Qt.ItemDataRole.UserRole)
        return None


class FilterPanel(QWidget):
    """筛选面板"""
    
    filters_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # 标题
        title = QLabel("筛选条件")
        title.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 文件类型筛选
        type_group = QGroupBox("文件类型")
        type_layout = QVBoxLayout(type_group)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(['全部', '文档 (.docx)', '表格 (.xlsx)', 
                                  '文本 (.txt)', '代码 (.py/.java)', '其他'])
        self.type_combo.currentIndexChanged.connect(self.emit_filters)
        type_layout.addWidget(self.type_combo)
        
        layout.addWidget(type_group)
        
        # 文件大小筛选
        size_group = QGroupBox("文件大小")
        size_layout = QVBoxLayout(size_group)
        
        self.size_min = QSpinBox()
        self.size_min.setRange(0, 1000000)
        self.size_min.setSuffix(" KB")
        self.size_min.setValue(0)
        
        self.size_max = QSpinBox()
        self.size_max.setRange(0, 1000000)
        self.size_max.setSuffix(" KB")
        self.size_max.setValue(0)
        self.size_max.setSpecialValueText("不限")
        
        size_layout.addWidget(QLabel("最小:"))
        size_layout.addWidget(self.size_min)
        size_layout.addWidget(QLabel("最大:"))
        size_layout.addWidget(self.size_max)
        
        # 启用大小筛选
        self.size_enabled = QCheckBox("启用大小筛选")
        self.size_enabled.stateChanged.connect(self.emit_filters)
        size_layout.addWidget(self.size_enabled)
        
        layout.addWidget(size_group)
        
        # 修改时间筛选
        time_group = QGroupBox("修改时间")
        time_layout = QVBoxLayout(time_group)
        
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        
        time_layout.addWidget(QLabel("从:"))
        time_layout.addWidget(self.date_from)
        time_layout.addWidget(QLabel("到:"))
        time_layout.addWidget(self.date_to)
        
        # 启用时间筛选
        self.time_enabled = QCheckBox("启用时间筛选")
        self.time_enabled.stateChanged.connect(self.emit_filters)
        time_layout.addWidget(self.time_enabled)
        
        layout.addWidget(time_group)
        
        # 搜索选项
        options_group = QGroupBox("搜索选项")
        options_layout = QVBoxLayout(options_group)
        
        self.fuzzy_search = QCheckBox("模糊搜索")
        self.fuzzy_search.setChecked(True)
        self.fuzzy_search.stateChanged.connect(self.emit_filters)
        options_layout.addWidget(self.fuzzy_search)
        
        self.content_search = QCheckBox("搜索文件内容")
        self.content_search.setChecked(True)
        self.content_search.stateChanged.connect(self.emit_filters)
        options_layout.addWidget(self.content_search)
        
        layout.addWidget(options_group)
        
        # 重置按钮
        reset_btn = QPushButton("重置筛选")
        reset_btn.clicked.connect(self.reset_filters)
        layout.addWidget(reset_btn)
        
        layout.addStretch()
    
    def get_filters(self) -> Dict[str, Any]:
        """获取当前筛选条件"""
        filters = {}
        
        # 文件类型
        type_map = {
            0: [],  # 全部
            1: ['.docx', '.doc'],
            2: ['.xlsx', '.xls'],
            3: ['.txt', '.md'],
            4: ['.py', '.java', '.cpp', '.h', '.js'],
            5: [],  # 其他
        }
        
        type_idx = self.type_combo.currentIndex()
        if type_idx > 0 and type_idx < 5:
            filters['extensions'] = type_map[type_idx]
        
        # 文件大小
        if self.size_enabled.isChecked():
            min_kb = self.size_min.value()
            max_kb = self.size_max.value() if self.size_max.value() > 0 else None
            
            if min_kb > 0:
                filters['min_size'] = min_kb * 1024
            if max_kb and max_kb > min_kb:
                filters['max_size'] = max_kb * 1024
        
        # 修改时间
        if self.time_enabled.isChecked():
            from_date = self.date_from.date().toPyDate()
            to_date = self.date_to.date().toPyDate()
            filters['modified_after'] = from_date
            filters['modified_before'] = to_date
        
        # 搜索选项
        filters['fuzzy'] = self.fuzzy_search.isChecked()
        filters['search_content'] = self.content_search.isChecked()
        
        return filters
    
    def emit_filters(self):
        """发送筛选条件变更信号"""
        self.filters_changed.emit(self.get_filters())
    
    def reset_filters(self):
        """重置筛选条件"""
        self.type_combo.setCurrentIndex(0)
        self.size_min.setValue(0)
        self.size_max.setValue(0)
        self.size_enabled.setChecked(False)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_to.setDate(QDate.currentDate())
        self.time_enabled.setChecked(False)
        self.fuzzy_search.setChecked(True)
        self.content_search.setChecked(True)
        
        self.emit_filters()


class AIAnswerArea(QTextEdit):
    """AI 回答显示区域"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        self.setReadOnly(True)
        self.setFont(QFont("Microsoft YaHei", 11))
        self.setPlaceholderText("AI 回答将显示在这里...")
        self.setMinimumHeight(150)
        
        # 设置样式
        self.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 10px;
            }
        """)
    
    def display_answer(self, answer: str, is_ai: bool = True):
        """显示回答"""
        prefix = "🤖 AI 回答:\n\n" if is_ai else "📋 搜索结果:\n\n"
        self.setText(prefix + answer)
    
    def clear_answer(self):
        """清空回答"""
        self.clear()


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self, indexer=None, ai_engine=None, config=None):
        super().__init__()
        
        self.indexer = indexer
        self.ai_engine = ai_engine
        self.config = config or get_config()
        self.logger = logger.bind(module="gui")
        
        # 搜索历史
        self.search_history = []
        self.max_history = 50
        
        # 初始化界面
        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_statusbar()
        self.setup_shortcuts()
        
        # 加载设置
        self.load_settings()
        
        # 连接信号
        self.connect_signals()
        
        # 初始化状态
        self.update_status()

        # 搜索线程
        self.search_thread = None
        self.ai_search_thread = None
    
    def setup_ui(self):
        """设置界面"""
        # 设置窗口属性
        self.setWindowTitle("Smart File Search - 智能文件搜索")
        self.setMinimumSize(1000, 700)
        self.resize(
            self.config.gui.window_width,
            self.config.gui.window_height
        )
        
        # 应用主题
        self.apply_theme()
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧面板（筛选器）
        self.filter_panel = FilterPanel()
        self.filter_panel.setMaximumWidth(280)
        self.filter_panel.setMinimumWidth(250)
        
        # 右侧面板
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(10)
        
        # 搜索框区域
        search_frame = QFrame()
        search_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        search_layout = QHBoxLayout(search_frame)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入搜索内容或自然语言查询...")
        self.search_input.setFont(QFont("Microsoft YaHei", 12))
        self.search_input.setMinimumHeight(40)
        
        self.search_btn = QPushButton("搜索")
        self.search_btn.setMinimumHeight(40)
        self.search_btn.setMinimumWidth(100)
        
        self.ai_btn = QPushButton("AI 搜索")
        self.ai_btn.setMinimumHeight(40)
        self.ai_btn.setMinimumWidth(100)
        self.ai_btn.setEnabled(self.config.ai.enabled)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        search_layout.addWidget(self.ai_btn)
        
        right_layout.addWidget(search_frame)
        
        # AI 回答区域
        ai_group = QGroupBox("AI 智能回答")
        ai_layout = QVBoxLayout(ai_group)
        
        self.ai_answer_area = AIAnswerArea()
        ai_layout.addWidget(self.ai_answer_area)
        
        right_layout.addWidget(ai_group)
        
        # 搜索结果区域
        results_group = QGroupBox("搜索结果")
        results_layout = QVBoxLayout(results_group)
        
        self.result_table = SearchResultTable()
        results_layout.addWidget(self.result_table)
        
        # 结果信息标签
        self.result_info_label = QLabel("共 0 个结果")
        results_layout.addWidget(self.result_info_label)
        
        right_layout.addWidget(results_group, stretch=1)
        
        # 使用分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.filter_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([250, 750])
        
        main_layout.addWidget(splitter)
    
    def setup_menu(self):
        """设置菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        # 新建索引
        new_index_action = QAction("新建索引(&N)", self)
        new_index_action.setShortcut(QKeySequence.StandardKey.New)
        new_index_action.triggered.connect(self.create_new_index)
        file_menu.addAction(new_index_action)
        
        # 更新索引
        update_index_action = QAction("更新索引(&U)", self)
        update_index_action.setShortcut(QKeySequence("F5"))
        update_index_action.triggered.connect(self.update_index)
        file_menu.addAction(update_index_action)
        
        file_menu.addSeparator()
        
        # 打开文件
        open_action = QAction("打开文件(&O)", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_selected_file)
        file_menu.addAction(open_action)
        
        # 打开所在文件夹
        open_folder_action = QAction("打开所在文件夹(&D)", self)
        open_folder_action.setShortcut(QKeySequence("Ctrl+D"))
        open_folder_action.triggered.connect(self.open_containing_folder)
        file_menu.addAction(open_folder_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑(&E)")
        
        # 复制路径
        copy_path_action = QAction("复制文件路径(&C)", self)
        copy_path_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_path_action.triggered.connect(self.copy_file_path)
        edit_menu.addAction(copy_path_action)
        
        # 设置菜单
        settings_menu = menubar.addMenu("设置(&S)")
        
        # 配置文件
        config_action = QAction("设置(&S)", self)
        config_action.triggered.connect(self.open_config_file)
        settings_menu.addAction(config_action)
        
        # AI 设置
        ai_settings_action = QAction("AI 设置(&A)", self)
        ai_settings_action.triggered.connect(self.show_ai_settings)
        settings_menu.addAction(ai_settings_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        # 关于
        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # 检查更新
        update_action = QAction("检查更新(&U)", self)
        update_action.triggered.connect(self.check_for_updates)
        help_menu.addAction(update_action)
    
    def setup_toolbar(self):
        """设置工具栏"""
        toolbar = self.addToolBar("主工具栏")
        toolbar.setMovable(False)
        
        # 后退/前进
        self.back_btn = QAction("←", self)
        self.back_btn.setToolTip("后退")
        self.back_btn.triggered.connect(self.go_back)
        toolbar.addAction(self.back_btn)
        
        self.forward_btn = QAction("→", self)
        self.forward_btn.setToolTip("前进")
        self.forward_btn.triggered.connect(self.go_forward)
        toolbar.addAction(self.forward_btn)
        
        toolbar.addSeparator()
        
        # 刷新索引
        refresh_action = QAction("🔄 刷新索引", self)
        refresh_action.setToolTip("刷新文件索引")
        refresh_action.triggered.connect(self.update_index)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        # 设置
        settings_action = QAction("⚙️ 设置", self)
        settings_action.setToolTip("打开设置")
        settings_action.triggered.connect(self.show_ai_settings)
        toolbar.addAction(settings_action)
    
    def setup_statusbar(self):
        """设置状态栏"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.statusbar.addWidget(self.status_label, stretch=1)
        
        # 索引信息
        self.index_info_label = QLabel("索引: 0 个文件")
        self.statusbar.addPermanentWidget(self.index_info_label)
        
        # AI 状态
        self.ai_status_label = QLabel("AI: 禁用")
        self.statusbar.addPermanentWidget(self.ai_status_label)
    
    def setup_shortcuts(self):
        """设置快捷键"""
        # Ctrl+F 聚焦搜索框
        focus_search = QShortcut(QKeySequence("Ctrl+F"), self)
        focus_search.activated.connect(self.search_input.setFocus)
        
        # Escape 清空搜索
        clear_search = QShortcut(QKeySequence("Escape"), self)
        clear_search.activated.connect(self.clear_search)
        
        # F3 下一个结果
        next_result = QShortcut(QKeySequence("F3"), self)
        next_result.activated.connect(self.select_next_result)
        
        # Shift+F3 上一个结果
        prev_result = QShortcut(QKeySequence("Shift+F3"), self)
        prev_result.activated.connect(self.select_prev_result)
    
    def connect_signals(self):
        """连接信号槽"""
        # 搜索相关
        self.search_input.textChanged.connect(self.on_search_text_changed)
        self.search_input.returnPressed.connect(self.perform_search)
        self.search_btn.clicked.connect(self.perform_search)
        self.ai_btn.clicked.connect(self.perform_ai_search)
        
        # 筛选器
        self.filter_panel.filters_changed.connect(self.on_filters_changed)
        
        # 结果表格
        self.result_table.itemSelectionChanged.connect(self.on_selection_changed)
        self.result_table.cellClicked.connect(self.on_cell_clicked)
    
    def apply_theme(self):
        """应用主题"""
        theme = self.config.gui.theme
        
        if theme == "dark":
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1e1e1e;
                }
                QWidget {
                    background-color: #2b2b2b;
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
                QLineEdit {
                    background-color: #3c3c3c;
                    border: 1px solid #555;
                    border-radius: 5px;
                    padding: 5px 10px;
                    color: #ffffff;
                }
                QLineEdit:focus {
                    border: 1px solid #0078d4;
                }
                QPushButton {
                    background-color: #0078d4;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 16px;
                    color: white;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1e8ae6;
                }
                QPushButton:pressed {
                    background-color: #006cbd;
                }
                QPushButton:disabled {
                    background-color: #555;
                    color: #999;
                }
                QTableWidget {
                    background-color: #2b2b2b;
                    border: 1px solid #555;
                    gridline-color: #444;
                    color: #ffffff;
                }
                QTableWidget::item {
                    padding: 5px;
                    color: #ffffff;
                }
                QTableWidget::item:selected {
                    background-color: #0078d4;
                    color: #ffffff;
                }
                QTableWidget::item:alternate {
                    background-color: #333333;
                    color: #ffffff;
                }
                QHeaderView::section {
                    background-color: #3c3c3c;
                    padding: 5px;
                    border: 1px solid #555;
                    font-weight: bold;
                    color: #ffffff;
                }
                QComboBox {
                    background-color: #3c3c3c;
                    border: 1px solid #555;
                    border-radius: 3px;
                    padding: 5px;
                    color: white;
                }
                QSpinBox {
                    background-color: #3c3c3c;
                    border: 1px solid #555;
                    border-radius: 3px;
                    padding: 5px;
                    color: white;
                }
                QDateEdit {
                    background-color: #3c3c3c;
                    border: 1px solid #555;
                    border-radius: 3px;
                    padding: 5px;
                    color: white;
                }
                QCheckBox {
                    color: white;
                }
                QMenuBar {
                    background-color: #2b2b2b;
                    color: white;
                }
                QMenuBar::item:selected {
                    background-color: #0078d4;
                }
                QMenu {
                    background-color: #2b2b2b;
                    color: white;
                    border: 1px solid #555;
                }
                QMenu::item:selected {
                    background-color: #0078d4;
                }
                QStatusBar {
                    background-color: #007acc;
                    color: white;
                }
                QToolBar {
                    background-color: #2b2b2b;
                    border: none;
                    spacing: 5px;
                }
                QSplitter::handle {
                    background-color: #555;
                }
            """)
        else:
            # Light theme
            self.setStyleSheet("")
    
    def load_settings(self):
        """加载设置"""
        settings = QSettings("SmartFileSearch", "SmartFileSearch")
        
        # 窗口几何
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        # 窗口状态
        state = settings.value("windowState")
        if state:
            self.restoreState(state)
        
        # 搜索历史
        history = settings.value("searchHistory", [])
        if history:
            self.search_history = history[:self.max_history]
    
    def save_settings(self):
        """保存设置"""
        settings = QSettings("SmartFileSearch", "SmartFileSearch")
        
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        settings.setValue("searchHistory", self.search_history)
    
    def update_status(self):
        """更新状态"""
        # 更新索引信息
        if self.indexer and hasattr(self.indexer, 'get_file_count'):
            try:
                count = self.indexer.get_file_count()
                self.index_info_label.setText(f"索引: {count} 个文件")
            except Exception as e:
                self.logger.error(f"获取文件数量失败: {e}")
                self.index_info_label.setText("索引: 未知")
        else:
            self.index_info_label.setText("索引: 未初始化")

        # 更新 AI 状态
        if self.ai_engine and self.ai_engine.is_enabled():
            self.ai_status_label.setText("AI: 启用")
            self.ai_btn.setEnabled(True)
        else:
            self.ai_status_label.setText("AI: 禁用")
            self.ai_btn.setEnabled(False)

    def on_search_text_changed(self, text: str):
        """搜索文本变化 - 不自动搜索，只更新状态"""
        # 不再自动搜索，等待用户按Enter键或点击搜索按钮
        if text.strip():
            self.status_label.setText("按Enter键或点击搜索按钮开始搜索")
        else:
            self.status_label.setText("就绪")
    
    def perform_search(self):
        """执行普通搜索"""
        query = self.search_input.text().strip()
        if not query:
            return

        # 如果有正在进行的搜索，等待它完成
        if self.search_thread and self.search_thread.isRunning():
            return

        # 添加到搜索历史
        if query not in self.search_history:
            self.search_history.insert(0, query)
            self.search_history = self.search_history[:self.max_history]

        # 获取筛选条件
        filters = self.filter_panel.get_filters()

        # 更新UI状态
        self.status_label.setText("搜索中...")
        self.ai_answer_area.display_answer("正在搜索...", is_ai=False)

        # 创建搜索线程
        self.search_thread = SearchThread(
            self.indexer,
            query,
            self.config.gui.max_results,
            filters
        )
        self.search_thread.finished.connect(self._on_search_finished)
        self.search_thread.error.connect(self._on_search_error)
        self.search_thread.start()

    def _on_search_finished(self, results: List[Dict], elapsed: float):
        """搜索完成回调"""
        # 显示结果
        self.result_table.display_results(results)
        self.result_info_label.setText(f"共 {len(results)} 个结果 ({elapsed:.2f}秒)")

        # 更新状态
        self.status_label.setText(f"搜索完成，找到 {len(results)} 个结果")

        # 生成简单回答
        if results:
            answer = self._generate_simple_answer(results)
            self.ai_answer_area.display_answer(answer, is_ai=False)
        else:
            self.ai_answer_area.display_answer("未找到匹配的文件。", is_ai=False)

    def _on_search_error(self, error_msg: str):
        """搜索错误回调"""
        self.logger.error(f"搜索失败: {error_msg}")
        QMessageBox.warning(self, "搜索错误", f"搜索失败: {error_msg}")
        self.status_label.setText("搜索失败")
        self.ai_answer_area.display_answer(f"搜索失败: {error_msg}", is_ai=False)
    
    def perform_ai_search(self):
        """执行 AI 搜索"""
        query = self.search_input.text().strip()
        if not query:
            return

        if not self.ai_engine or not self.ai_engine.is_enabled():
            QMessageBox.warning(self, "AI 未启用", "AI 功能未启用，请在设置中启用 AI 功能。")
            return

        # 如果有正在进行的AI搜索，等待它完成
        if self.ai_search_thread and self.ai_search_thread.isRunning():
            return

        self.status_label.setText("AI 分析中...")
        self.ai_answer_area.display_answer("正在分析您的查询，请稍候...", is_ai=True)

        # 获取筛选条件
        filters = self.filter_panel.get_filters()

        # 创建AI搜索线程
        self.ai_search_thread = AISearchThread(
            self.ai_engine,
            self.indexer,
            query,
            self.config.gui.max_results,
            filters
        )
        self.ai_search_thread.finished.connect(self._on_ai_search_finished)
        self.ai_search_thread.error.connect(self._on_ai_search_error)
        self.ai_search_thread.start()

    def _on_ai_search_finished(self, analysis, results: List[Dict], elapsed: float):
        """AI搜索完成回调"""
        self.logger.debug(f"AI 分析结果: {analysis}")

        # 显示结果
        self.result_table.display_results(results)
        self.result_info_label.setText(f"共 {len(results)} 个结果 (置信度: {analysis.confidence:.0%})")

        # 生成 AI 回答
        query = self.search_input.text().strip()
        if results:
            # 在后台线程中生成AI回答
            self.ai_answer_area.display_answer("正在生成回答...", is_ai=True)
            # 使用QTimer延迟执行，避免阻塞UI
            QTimer.singleShot(100, lambda: self._generate_ai_answer(query, results, analysis))
        else:
            answer = f"未找到与 '{query}' 相关的文件。\n\nAI 分析: {analysis.intent}"
            self.ai_answer_area.display_answer(answer, is_ai=True)
            self.status_label.setText("AI 搜索完成")

    def _generate_ai_answer(self, query: str, results: List[Dict], analysis):
        """生成AI回答"""
        try:
            answer = self.ai_engine.generate_answer(query, results)
            answer += f"\n\n意图分析: {analysis.intent}"
            self.ai_answer_area.display_answer(answer, is_ai=True)
            self.status_label.setText("AI 搜索完成")
        except Exception as e:
            self.logger.error(f"AI 生成回答失败: {e}")
            self.ai_answer_area.display_answer(f"AI 生成回答失败: {str(e)}", is_ai=True)
            self.status_label.setText("AI 搜索失败")

    def _on_ai_search_error(self, error_msg: str):
        """AI搜索错误回调"""
        self.logger.error(f"AI 搜索失败: {error_msg}")
        self.ai_answer_area.display_answer(f"AI 搜索失败: {error_msg}", is_ai=True)
        self.status_label.setText("AI 搜索失败")
    
    def _generate_simple_answer(self, results: List[Dict]) -> str:
        """生成简单回答"""
        if not results:
            return "未找到匹配的文件。"
        
        lines = [f"找到 {len(results)} 个相关文件：\n"]
        
        for i, result in enumerate(results[:10], 1):
            filename = result.get('filename', '未知')
            size = result.get('size', 0)
            size_str = self.result_table._format_size(size)
            
            lines.append(f"{i}. {filename} ({size_str})")
            
            # 添加高亮片段
            highlights = result.get('highlights', '')
            if highlights:
                lines.append(f"   匹配: {highlights[:100]}...")
        
        if len(results) > 10:
            lines.append(f"\n... 还有 {len(results) - 10} 个结果")
        
        return '\n'.join(lines)
    
    def on_filters_changed(self, filters: Dict):
        """筛选条件变化"""
        # 如果有搜索内容，重新搜索
        if self.search_input.text().strip():
            self.perform_search()
    
    def on_selection_changed(self):
        """选择变化"""
        pass
    
    def on_cell_clicked(self, row: int, column: int):
        """单元格点击"""
        result = self.result_table.get_selected_file()
        if result:
            # 可以在这里显示预览
            pass
    
    def clear_search(self):
        """清空搜索"""
        self.search_input.clear()
        self.result_table.setRowCount(0)
        self.ai_answer_area.clear_answer()
        self.result_info_label.setText("共 0 个结果")
        self.status_label.setText("就绪")
    
    def select_next_result(self):
        """选择下一个结果"""
        current_row = self.result_table.currentRow()
        if current_row < self.result_table.rowCount() - 1:
            self.result_table.selectRow(current_row + 1)
    
    def select_prev_result(self):
        """选择上一个结果"""
        current_row = self.result_table.currentRow()
        if current_row > 0:
            self.result_table.selectRow(current_row - 1)
    
    def go_back(self):
        """后退"""
        # TODO: 实现搜索历史导航
        pass
    
    def go_forward(self):
        """前进"""
        # TODO: 实现搜索历史导航
        pass
    
    def create_new_index(self):
        """创建新索引"""
        reply = QMessageBox.question(
            self,
            "创建新索引",
            "这将删除现有索引并重新创建。确定要继续吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._do_index(incremental=False)
    
    def update_index(self):
        """更新索引"""
        self._do_index(incremental=True)
    
    def _do_index(self, incremental: bool = False):
        """执行索引操作"""
        # 创建详细的进度对话框
        title = "更新索引" if incremental else "创建索引"
        progress_dialog = IndexProgressDialog(title, self)
        progress_dialog.show()

        # 取消标志
        cancel_flag = [False]  # 使用列表以便在闭包中修改

        # 进度回调函数
        def progress_callback(current, total, filename, status):
            """索引进度回调"""
            if cancel_flag[0] or progress_dialog.was_cancelled():
                return False  # 返回 False 表示应该取消
            self.worker.progress.emit(current, total, filename, status)
            return True

        def index_task():
            return self.indexer.create_index(
                self.config.index.directories,
                incremental=incremental,
                progress_callback=progress_callback
            )

        # 使用工作线程
        self.worker = WorkerThread(index_task)

        # 取消处理函数
        def on_cancel():
            cancel_flag[0] = True
            # 等待线程结束（最多等待2秒）
            if not self.worker.wait(2000):
                # 如果线程不结束，强制终止
                self.worker.terminate()
                self.worker.wait(500)
            progress_dialog.close_with_cancel()
            self.status_label.setText("索引已取消")

        # 连接信号
        progress_dialog.cancelled.connect(on_cancel)
        self.worker.progress.connect(
            lambda curr, total, fname, status: progress_dialog.update_progress(curr, total, fname, status)
        )
        self.worker.finished.connect(lambda stats: self._on_index_complete(stats, progress_dialog))
        self.worker.error.connect(lambda err: self._on_index_error(err, progress_dialog))

        self.worker.start()
    
    def _on_index_complete(self, stats: Dict, progress: IndexProgressDialog):
        """索引完成"""
        progress.close()

        self.update_status()

        # 检查是否被取消
        if stats.get('cancelled', False):
            duration = stats.get('duration', 0)
            self.status_label.setText("索引已取消")
            return

        # 显示完成信息
        duration = stats.get('duration', 0)
        QMessageBox.information(
            self,
            "索引完成",
            f"索引完成！\n\n"
            f"总文件数: {stats.get('total_files', 0)}\n"
            f"已索引: {stats.get('indexed_files', 0)}\n"
            f"跳过: {stats.get('skipped_files', 0)}\n"
            f"失败: {stats.get('failed_files', 0)}\n"
            f"耗时: {duration:.2f} 秒"
        )

        self.status_label.setText("索引完成")
    
    def _on_index_error(self, error: str, progress: IndexProgressDialog):
        """索引错误"""
        progress.close()

        QMessageBox.critical(self, "索引错误", f"索引创建失败:\n{error}")
        self.status_label.setText("索引失败")
    
    def open_selected_file(self):
        """打开选中的文件"""
        result = self.result_table.get_selected_file()
        if result:
            path = result.get('path', '')
            if Path(path).exists():
                QDesktopServices.openUrl(Path(path).as_uri())
    
    def open_containing_folder(self):
        """打开文件所在文件夹"""
        result = self.result_table.get_selected_file()
        if result:
            path = result.get('path', '')
            folder = Path(path).parent
            if folder.exists():
                QDesktopServices.openUrl(folder.as_uri())
    
    def copy_file_path(self):
        """复制文件路径"""
        result = self.result_table.get_selected_file()
        if result:
            path = result.get('path', '')
            QApplication.clipboard().setText(path)
            self.status_label.setText("路径已复制到剪贴板")
    
    def open_config_file(self):
        """打开设置对话框"""
        try:
            from .settings_dialog import SettingsDialog
        except ImportError:
            from settings_dialog import SettingsDialog

        try:
            dialog = SettingsDialog(self.config, self)
            dialog.config_changed.connect(self._on_config_changed)
            dialog.exec()

        except Exception as e:
            self.logger.error(f"打开设置对话框失败: {e}")
            QMessageBox.critical(
                self,
                "错误",
                f"打开设置对话框失败:\n{str(e)}\n\n请查看日志获取详细信息。"
            )
    
    def _on_config_changed(self):
        """配置已更改"""
        # 重新加载配置
        from .config import reload_config
        try:
            reload_config
        except ImportError:
            from config import reload_config

        self.config = reload_config()

        # 重新初始化AI引擎（如果AI设置有变化）
        try:
            from .ai_engine import close_ai_engine, get_ai_engine
        except ImportError:
            from ai_engine import close_ai_engine, get_ai_engine

        # 关闭旧的AI引擎
        close_ai_engine()

        # 重新创建AI引擎
        self.ai_engine = get_ai_engine(self.config)

        # 更新UI状态
        self.update_status()

        # 显示提示
        if self.config.ai.enabled:
            model_path = Path(self.config.ai.model_path).expanduser()
            if model_path.exists():
                self.status_label.setText(f"设置已保存，AI 功能已启用")
            else:
                self.status_label.setText(f"设置已保存，但 AI 模型文件不存在")
        else:
            self.status_label.setText("设置已保存，AI 功能已禁用")
    
    def show_ai_settings(self):
        """显示 AI 设置对话框"""
        # TODO: 实现 AI 设置对话框
        QMessageBox.information(
            self,
            "AI 设置",
            f"AI 功能状态: {'启用' if self.config.ai.enabled else '禁用'}\n\n"
            f"模型路径: {self.config.ai.model_path}\n"
            f"上下文大小: {self.config.ai.context_size}\n\n"
            f"请编辑配置文件来修改 AI 设置。"
        )
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于 Smart File Search",
            """<h2>Smart File Search</h2>
            <p>版本 1.0.0</p>
            <p>智能本地文件搜索工具</p>
            <p>结合了 Everything 的快速文件索引和本地 AI 理解能力。</p>
            <p>&copy; 2024 Smart File Search Team</p>
            <hr>
            <p>技术栈: Python, PyQt6, Whoosh, llama.cpp</p>
            """
        )
    
    def check_for_updates(self):
        """检查更新"""
        # TODO: 实现更新检查
        QMessageBox.information(self, "检查更新", "您正在使用最新版本。")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 保存设置
        self.save_settings()

        # 等待搜索线程完成
        if hasattr(self, 'search_thread') and self.search_thread and self.search_thread.isRunning():
            self.search_thread.quit()
            self.search_thread.wait(500)

        # 等待AI搜索线程完成
        if hasattr(self, 'ai_search_thread') and self.ai_search_thread and self.ai_search_thread.isRunning():
            self.ai_search_thread.quit()
            self.ai_search_thread.wait(500)

        # 关闭工作线程
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()

        event.accept()


def run_gui(indexer=None, ai_engine=None, config=None):
    """运行 GUI 应用"""
    app = QApplication(sys.argv)
    app.setApplicationName("Smart File Search")
    app.setOrganizationName("SmartFileSearch")
    
    # 设置字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    # 创建主窗口
    window = MainWindow(indexer, ai_engine, config)
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(run_gui())