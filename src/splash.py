#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动画面模块
显示加载进度，避免用户以为程序没启动
"""

import sys
from PyQt6.QtWidgets import QSplashScreen, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont


class SplashScreen(QSplashScreen):
    """启动画面"""
    
    def __init__(self):
        # 创建一个简单的启动画面
        pixmap = QPixmap(500, 300)
        pixmap.fill(QColor(45, 45, 45))
        
        super().__init__(pixmap)
        
        # 设置样式
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        
        # 绘制内容
        self._draw_content()
        
    def _draw_content(self):
        """绘制启动画面内容"""
        painter = QPainter(self)
        
        # 背景
        painter.fillRect(self.rect(), QColor(45, 45, 45))
        
        # 标题
        font = QFont("Microsoft YaHei", 24, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Smart File Search")
        
        # 副标题
        font = QFont("Microsoft YaHei", 12)
        painter.setFont(font)
        painter.setPen(QColor(180, 180, 180))
        subtitle_rect = self.rect()
        subtitle_rect.moveTop(subtitle_rect.top() + 40)
        painter.drawText(subtitle_rect, Qt.AlignmentFlag.AlignCenter, "AI-Powered Local File Search")
        
        # 加载提示
        font = QFont("Microsoft YaHei", 10)
        painter.setFont(font)
        painter.setPen(QColor(120, 120, 120))
        loading_rect = self.rect()
        loading_rect.moveTop(loading_rect.top() + 80)
        painter.drawText(loading_rect, Qt.AlignmentFlag.AlignCenter, "正在加载...")
        
        painter.end()
        
    def showMessage(self, message):
        """显示加载消息"""
        self._draw_content()
        
        painter = QPainter(self)
        
        # 加载消息
        font = QFont("Microsoft YaHei", 10)
        painter.setFont(font)
        painter.setPen(QColor(100, 200, 100))
        
        loading_rect = self.rect()
        loading_rect.moveTop(loading_rect.top() + 80)
        painter.drawText(loading_rect, Qt.AlignmentFlag.AlignCenter, message)
        
        painter.end()
        
        # 强制刷新
        self.repaint()
        QApplication.processEvents()


def show_splash():
    """显示启动画面"""
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    splash = SplashScreen()
    splash.show()
    
    return splash


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    splash = show_splash()
    
    # 模拟加载
    import time
    messages = [
        "初始化界面...",
        "加载配置文件...",
        "初始化搜索引擎...",
        "准备完成！"
    ]
    
    for msg in messages:
        splash.showMessage(msg)
        time.sleep(0.5)
    
    splash.close()
    sys.exit(0)
