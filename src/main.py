#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主程序入口
添加启动画面，优化用户体验
"""

import sys
import os
from pathlib import Path
from loguru import logger

# 获取程序运行目录
if getattr(sys, 'frozen', False):
    # PyInstaller 打包后的路径
    application_path = Path(sys.executable).parent
else:
    # 开发环境路径
    application_path = Path(__file__).parent.parent

# 添加到 Python 路径
sys.path.insert(0, str(application_path))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# 导入启动画面
try:
    from src.splash import SplashScreen
except ImportError:
    # 打包后的导入方式
    from splash import SplashScreen

# 导入主窗口
try:
    from src.gui import MainWindow
    from src.config import get_config
    from src.index import FileIndexer
except ImportError:
    # 打包后的导入方式
    from gui import MainWindow
    from config import get_config
    from index import FileIndexer


def main():
    """主函数"""
    # 高DPI支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("Smart File Search")
    app.setApplicationVersion("1.0.0")
    
    # 显示启动画面
    splash = SplashScreen()
    splash.show()
    
    # 强制处理事件
    app.processEvents()
    
    try:
        # 加载配置
        splash.showMessage("加载配置...")
        app.processEvents()
        config = get_config()
        
        # 初始化搜索引擎
        splash.showMessage("初始化搜索引擎...")
        app.processEvents()
        
        # 创建索引器
        indexer = FileIndexer(
            index_dir=Path(config.index.index_dir).expanduser(),
            supported_extensions=config.index.supported_extensions
        )
        
        # 初始化主窗口
        splash.showMessage("初始化界面...")
        app.processEvents()
        
        window = MainWindow(indexer=indexer, config=config)
        
        # 延迟加载AI（如果启用）
        if config.ai.enabled:
            splash.showMessage("准备AI模块...")
            app.processEvents()
            # AI模块将在后台线程中加载
        
        # 完成
        splash.showMessage("准备完成！")
        app.processEvents()
        
        # 短暂延迟后关闭启动画面
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(500, splash.close)
        
        # 显示主窗口
        window.show()
        
        # 运行应用
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"启动失败: {e}")
        splash.close()
        
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(
            None,
            "启动错误",
            f"程序启动失败:\n\n{str(e)}\n\n请检查日志文件。"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
