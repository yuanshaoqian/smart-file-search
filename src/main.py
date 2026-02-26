#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主程序入口
添加启动画面，优化用户体验
"""

import sys
import os
import atexit
from pathlib import Path
from datetime import datetime

# 获取程序运行目录
if getattr(sys, 'frozen', False):
    # PyInstaller 打包后的路径
    application_path = Path(sys.executable).parent
else:
    # 开发环境路径
    application_path = Path(__file__).parent.parent

# 添加到 Python 路径
sys.path.insert(0, str(application_path))

# 配置日志 - 在导入 loguru 之前配置
from loguru import logger

# 移除默认处理器
logger.remove()

# 配置日志目录
log_dir = application_path / "logs"
try:
    log_dir.mkdir(parents=True, exist_ok=True)
except Exception:
    pass

log_file = log_dir / f"smart_file_search_{datetime.now().strftime('%Y%m%d')}.log"

# 添加控制台日志（仅在 stderr 可用时）
if sys.stderr is not None:
    try:
        logger.add(
            sys.stderr,
            level="DEBUG",
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
    except Exception:
        pass

# 添加文件日志
try:
    logger.add(
        str(log_file),
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="7 days",
        encoding="utf-8"
    )
except Exception as e:
    # 如果文件日志失败，至少确保程序能运行
    pass

logger.info("=" * 50)
logger.info("Smart File Search 启动中...")
logger.info(f"程序路径: {application_path}")
logger.info(f"日志文件: {log_file}")
logger.info(f"Python 版本: {sys.version}")
logger.info(f"操作系统: {sys.platform}")

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

# 全局变量用于清理
_window = None
_config = None


def cleanup():
    """程序退出时的清理函数"""
    logger.info("程序正在退出，执行清理...")
    try:
        if _window:
            _window.save_settings()
            logger.info("设置已保存")
    except Exception as e:
        logger.error(f"清理时出错: {e}")
    logger.info("Smart File Search 已退出")
    logger.info("=" * 50)


def main():
    """主函数"""
    global _window, _config

    # 注册退出清理函数
    atexit.register(cleanup)

    # 高DPI支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("Smart File Search")
    app.setApplicationVersion("1.0.0")
    logger.info("QApplication 创建成功")

    # 显示启动画面
    splash = SplashScreen()
    splash.show()

    # 强制处理事件
    app.processEvents()

    try:
        # 加载配置
        splash.showMessage("加载配置...")
        app.processEvents()
        logger.info("正在加载配置...")
        config = get_config()
        _config = config
        logger.info(f"配置加载完成: AI启用={config.ai.enabled}, 索引目录={config.index.directories}")

        # 初始化搜索引擎
        splash.showMessage("初始化搜索引擎...")
        app.processEvents()
        logger.info("正在初始化搜索引擎...")
        index_dir = str(Path(config.index.index_dir).expanduser())
        indexer = FileIndexer(index_dir=index_dir, config=config)
        logger.info(f"搜索引擎初始化完成: 索引目录={index_dir}")

        # 初始化主窗口
        splash.showMessage("初始化界面...")
        app.processEvents()
        logger.info("正在初始化主窗口...")
        window = MainWindow(indexer=indexer, config=config)
        _window = window
        logger.info("主窗口初始化完成")

        # 延迟加载AI（如果启用）
        if config.ai.enabled:
            splash.showMessage("准备AI模块...")
            app.processEvents()
            logger.info("AI模块已启用，将在后台加载")

        # 完成
        splash.showMessage("准备完成！")
        app.processEvents()
        logger.info("启动完成，显示主窗口")

        # 短暂延迟后关闭启动画面
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(500, splash.close)

        # 显示主窗口
        window.show()

        # 运行应用
        exit_code = app.exec()
        logger.info(f"应用退出，退出码: {exit_code}")
        sys.exit(exit_code)

    except Exception as e:
        logger.error(f"启动失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        splash.close()

        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(
            None,
            "启动错误",
            f"程序启动失败:\n\n{str(e)}\n\n请检查日志文件:\n{log_file}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
