#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart File Search - 主程序入口
整合所有模块，提供命令行和图形界面启动
"""

import sys
import os
import argparse
from pathlib import Path
from typing import Optional

# 添加 src 目录到路径
src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from loguru import logger

from config import get_config, ConfigManager
from index import get_indexer, close_indexer
from ai_engine import get_ai_engine, close_ai_engine
from file_parser import get_parser


def setup_logging(config):
    """设置日志"""
    # 移除默认处理器
    logger.remove()
    
    # 添加控制台处理器
    log_level = config.logging.level
    
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # 添加文件处理器
    log_file = Path(config.logging.file).expanduser()
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        str(log_file),
        level=log_level,
        rotation=config.logging.max_size,
        retention=f"{config.logging.retention} days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        encoding="utf-8"
    )
    
    logger.info(f"日志系统初始化完成，级别: {log_level}")


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="Smart File Search - 智能文件搜索工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                    启动图形界面
  %(prog)s --init             初始化文件索引
  %(prog)s --search "报告"    命令行搜索
  %(prog)s --ai "上周的文档"  AI 自然语言搜索
  %(prog)s --debug            调试模式启动
        """
    )
    
    parser.add_argument(
        '--init', '-i',
        action='store_true',
        help='初始化文件索引（首次运行或重建索引）'
    )
    
    parser.add_argument(
        '--update', '-u',
        action='store_true',
        help='增量更新文件索引'
    )
    
    parser.add_argument(
        '--search', '-s',
        type=str,
        metavar='QUERY',
        help='命令行搜索模式'
    )
    
    parser.add_argument(
        '--ai', '-a',
        type=str,
        metavar='QUERY',
        help='AI 自然语言搜索'
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        metavar='FILE',
        help='指定配置文件路径'
    )
    
    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='启用调试模式'
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        help='无头模式（不启动图形界面）'
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version='Smart File Search 1.0.0'
    )
    
    return parser.parse_args()


def init_index(config):
    """初始化索引"""
    logger.info("开始初始化文件索引...")
    
    indexer = get_indexer(config.index.index_dir, config)
    
    stats = indexer.create_index(
        config.index.directories,
        incremental=False
    )
    
    logger.info(
        f"索引初始化完成: "
        f"总文件 {stats['total_files']}, "
        f"成功 {stats['indexed_files']}, "
        f"跳过 {stats['skipped_files']}, "
        f"失败 {stats['failed_files']}, "
        f"耗时 {stats['duration']:.2f}秒"
    )
    
    return indexer


def update_index(config):
    """增量更新索引"""
    logger.info("开始增量更新文件索引...")
    
    indexer = get_indexer(config.index.index_dir, config)
    
    stats = indexer.create_index(
        config.index.directories,
        incremental=True
    )
    
    logger.info(
        f"索引更新完成: "
        f"更新了 {stats['indexed_files']} 个文件, "
        f"耗时 {stats['duration']:.2f}秒"
    )
    
    return indexer


def cli_search(query: str, config, use_ai: bool = False):
    """命令行搜索"""
    indexer = get_indexer(config.index.index_dir, config)
    ai_engine = None
    
    if use_ai and config.ai.enabled:
        ai_engine = get_ai_engine(config)
    
    if use_ai and ai_engine and ai_engine.is_enabled():
        # AI 搜索
        print(f"\n🔍 AI 搜索: {query}")
        print("=" * 60)
        
        analysis = ai_engine.parse_natural_language(query)
        print(f"\n意图分析: {analysis.intent}")
        print(f"置信度: {analysis.confidence:.0%}")
        print(f"关键词: {', '.join(analysis.keywords)}")
        
        # 构建搜索查询
        search_query = " ".join(analysis.keywords) if analysis.keywords else query
        filters = analysis.filters
        
        results = indexer.search(search_query, limit=20, filters=filters)
        
        if results:
            print(f"\n找到 {len(results)} 个结果:")
            for i, result in enumerate(results, 1):
                print(f"\n{i}. {result['filename']}")
                print(f"   路径: {result['path']}")
                print(f"   大小: {result['size'] / 1024:.1f} KB")
                
                if result.get('highlights'):
                    print(f"   匹配: {result['highlights'][:100]}...")
            
            # 生成 AI 回答
            print("\n" + "=" * 60)
            print("AI 回答:")
            answer = ai_engine.generate_answer(query, results)
            print(answer)
        else:
            print("\n未找到匹配的文件。")
    
    else:
        # 普通搜索
        print(f"\n🔍 搜索: {query}")
        print("=" * 60)
        
        results = indexer.search(query, limit=20)
        
        if results:
            print(f"\n找到 {len(results)} 个结果:")
            for i, result in enumerate(results, 1):
                print(f"\n{i}. {result['filename']}")
                print(f"   路径: {result['path']}")
                print(f"   大小: {result['size'] / 1024:.1f} KB")
                print(f"   修改: {result['modified']}")
                
                if result.get('highlights'):
                    print(f"   匹配: {result['highlights'][:100]}...")
        else:
            print("\n未找到匹配的文件。")


def run_gui(config):
    """运行图形界面"""
    from gui import run_gui as _run_gui
    
    # 初始化索引器
    indexer = get_indexer(config.index.index_dir, config)
    
    # 检查是否需要初始化索引
    if indexer.get_file_count() == 0:
        logger.warning("索引为空，请先运行 --init 初始化索引")
        
        import tkinter as tk
        from tkinter import messagebox
        
        root = tk.Tk()
        root.withdraw()
        
        answer = messagebox.askyesno(
            "索引为空",
            "文件索引为空，是否立即创建索引？\n\n这可能需要几分钟时间。"
        )
        
        if answer:
            init_index(config)
    
    # 初始化 AI 引擎
    ai_engine = None
    if config.ai.enabled:
        logger.info("初始化 AI 引擎...")
        ai_engine = get_ai_engine(config)
    
    # 运行 GUI
    logger.info("启动图形界面...")
    return _run_gui(indexer, ai_engine, config)


def main():
    """主函数"""
    args = parse_arguments()
    
    # 加载配置
    config_path = args.config
    if args.debug:
        # 调试模式：设置日志级别为 DEBUG
        import tempfile
        # 临时修改默认配置
        from config import DEFAULT_CONFIG
        DEFAULT_CONFIG['logging']['level'] = 'DEBUG'
    
    config = get_config(config_path)
    
    # 设置日志
    setup_logging(config)
    
    logger.info("=" * 60)
    logger.info("Smart File Search 启动")
    logger.info(f"Python 版本: {sys.version}")
    logger.info(f"配置文件: {ConfigManager.get_default_config_path()}")
    logger.info("=" * 60)
    
    try:
        # 处理不同的运行模式
        if args.init:
            # 初始化索引
            init_index(config)
            
        elif args.update:
            # 更新索引
            update_index(config)
            
        elif args.search:
            # 命令行搜索
            cli_search(args.search, config, use_ai=False)
            
        elif args.ai:
            # AI 搜索
            cli_search(args.ai, config, use_ai=True)
            
        elif args.headless:
            # 无头模式
            logger.info("以无头模式运行...")
            indexer = get_indexer(config.index.index_dir, config)
            logger.info(f"当前索引文件数: {indexer.get_file_count()}")
            
        else:
            # 默认：启动图形界面
            return run_gui(config)
    
    except KeyboardInterrupt:
        logger.info("用户中断")
        return 0
    
    except Exception as e:
        logger.exception(f"程序异常: {e}")
        return 1
    
    finally:
        # 清理资源
        close_indexer()
        close_ai_engine()
        logger.info("程序退出")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())