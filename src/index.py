#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件索引模块
基于 Whoosh 的全文搜索引擎，支持增量更新
"""

import os
import time
import hashlib
import fnmatch
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

import whoosh
from whoosh import index
from whoosh.fields import Schema, TEXT, KEYWORD, ID, DATETIME, NUMERIC
from whoosh.qparser import QueryParser, MultifieldParser, OrGroup, FuzzyTermPlugin
from whoosh.query import Every, Term, And, Or, Not, DateRange, NumericRange
from whoosh.writing import AsyncWriter
from loguru import logger

from .file_parser import get_parser
from .config import get_config


@dataclass
class FileMetadata:
    """文件元数据"""
    path: str  # 文件路径
    filename: str  # 文件名
    extension: str  # 文件扩展名
    size: int  # 文件大小（字节）
    modified: datetime  # 修改时间
    created: datetime  # 创建时间
    content: Optional[str] = None  # 文件内容（可选）
    checksum: Optional[str] = None  # 文件内容校验和（用于检测变化）
    
    @classmethod
    def from_path(cls, file_path: str) -> Optional['FileMetadata']:
        """从文件路径创建元数据"""
        try:
            path_obj = Path(file_path)
            stat = path_obj.stat()
            
            return cls(
                path=str(path_obj.resolve()),
                filename=path_obj.name,
                extension=path_obj.suffix.lower(),
                size=stat.st_size,
                modified=datetime.fromtimestamp(stat.st_mtime),
                created=datetime.fromtimestamp(stat.st_ctime),
            )
        except Exception as e:
            logger.error(f"获取文件元数据失败 {file_path}: {e}")
            return None
    
    def calculate_checksum(self, content: Optional[str] = None) -> str:
        """计算文件校验和"""
        if content is None:
            content = self.content or ""
        
        # 使用文件名、大小、修改时间和内容计算校验和
        data = f"{self.path}:{self.size}:{self.modified.timestamp()}:{content}"
        return hashlib.md5(data.encode('utf-8')).hexdigest()


class FileIndexer:
    """文件索引器"""
    
    def __init__(self, index_dir: str, config=None):
        """
        初始化文件索引器
        
        Args:
            index_dir: 索引存储目录
            config: 应用程序配置
        """
        self.index_dir = Path(index_dir)
        self.config = config or get_config()
        self.logger = logger.bind(module="indexer")
        
        # 文件解析器
        self.parser = get_parser()
        
        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=self.config.advanced.parser_threads)
        
        # 索引架构
        self.schema = Schema(
            path=ID(stored=True, unique=True),  # 文件路径（唯一）
            filename=TEXT(stored=True),         # 文件名
            extension=KEYWORD(stored=True),     # 扩展名
            size=NUMERIC(stored=True),          # 文件大小
            modified=DATETIME(stored=True),     # 修改时间
            created=DATETIME(stored=True),      # 创建时间
            content=TEXT(stored=True),          # 文件内容
            checksum=ID(stored=True),           # 校验和（用于检测变化）
        )
        
        # 索引实例
        self.ix = None
        self._open_index()
    
    def _open_index(self) -> None:
        """打开或创建索引"""
        try:
            if index.exists_in(self.index_dir):
                self.ix = index.open_dir(self.index_dir)
                self.logger.info(f"打开现有索引: {self.index_dir}")
            else:
                self.index_dir.mkdir(parents=True, exist_ok=True)
                self.ix = index.create_in(self.index_dir, self.schema)
                self.logger.info(f"创建新索引: {self.index_dir}")
        except Exception as e:
            self.logger.error(f"打开索引失败: {e}")
            raise
    
    def _should_index(self, file_path: str) -> bool:
        """
        检查是否应该索引该文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否应该索引
        """
        path_obj = Path(file_path)
        
        # 检查文件大小
        try:
            file_size = path_obj.stat().st_size
            if file_size > self.config.index.max_file_size:
                return False
        except:
            return False
        
        # 检查扩展名
        ext = path_obj.suffix.lower()
        if ext not in self.config.index.supported_extensions:
            return False
        
        # 检查排除模式
        for pattern in self.config.index.exclude_patterns:
            if fnmatch.fnmatch(path_obj.name, pattern):
                return False
            if fnmatch.fnmatch(str(path_obj), pattern):
                return False
        
        # 检查隐藏文件
        if self.config.advanced.ignore_hidden and path_obj.name.startswith('.'):
            return False
        
        # 检查是否支持解析
        if not self.parser.is_supported(file_path):
            return False
        
        return True
    
    def _index_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        索引单个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            索引文档字典，如果失败则返回 None
        """
        if not self._should_index(file_path):
            return None
        
        # 获取文件元数据
        metadata = FileMetadata.from_path(file_path)
        if metadata is None:
            return None
        
        # 解析文件内容
        content = self.parser.parse(file_path)
        if content is None:
            # 仍然索引元数据，但没有内容
            content = ""
        
        metadata.content = content
        metadata.checksum = metadata.calculate_checksum(content)
        
        # 转换为索引文档
        doc = {
            'path': metadata.path,
            'filename': metadata.filename,
            'extension': metadata.extension,
            'size': metadata.size,
            'modified': metadata.modified,
            'created': metadata.created,
            'content': content,
            'checksum': metadata.checksum,
        }
        
        return doc
    
    def create_index(self, root_paths: List[str], incremental: bool = False) -> Dict[str, Any]:
        """
        创建或更新索引
        
        Args:
            root_paths: 要索引的根目录列表
            incremental: 是否增量更新（只更新变化文件）
            
        Returns:
            统计信息
        """
        stats = {
            'total_files': 0,
            'indexed_files': 0,
            'skipped_files': 0,
            'failed_files': 0,
            'start_time': time.time(),
            'end_time': None,
            'directories': root_paths,
        }
        
        self.logger.info(f"开始{'增量' if incremental else '全量'}索引: {root_paths}")
        
        # 收集所有文件
        all_files = []
        for root_path in root_paths:
            root = Path(root_path).expanduser().resolve()
            if not root.exists():
                self.logger.warning(f"目录不存在: {root}")
                continue
            
            for file_path in root.rglob('*'):
                if file_path.is_file():
                    all_files.append(str(file_path))
        
        stats['total_files'] = len(all_files)
        self.logger.info(f"找到 {stats['total_files']} 个文件")
        
        # 如果是增量更新，检查哪些文件需要更新
        files_to_index = all_files
        if incremental and self.ix.reader().doc_count() > 0:
            files_to_index = self._get_changed_files(all_files)
            self.logger.info(f"增量更新: {len(files_to_index)} 个文件需要更新")
        
        # 使用线程池并行处理文件
        writer = AsyncWriter(self.ix)
        futures = {}
        
        for file_path in files_to_index:
            future = self.executor.submit(self._index_file, file_path)
            futures[future] = file_path
        
        # 处理结果
        for future in as_completed(futures):
            file_path = futures[future]
            
            try:
                doc = future.result(timeout=30)
                if doc:
                    # 删除旧记录（如果存在）
                    writer.delete_by_term('path', doc['path'])
                    # 添加新记录
                    writer.add_document(**doc)
                    stats['indexed_files'] += 1
                    
                    if stats['indexed_files'] % 100 == 0:
                        self.logger.info(f"已索引 {stats['indexed_files']} 个文件")
                else:
                    stats['skipped_files'] += 1
                    
            except Exception as e:
                self.logger.error(f"索引文件失败 {file_path}: {e}")
                stats['failed_files'] += 1
        
        # 提交更改
        writer.commit()
        
        stats['end_time'] = time.time()
        stats['duration'] = stats['end_time'] - stats['start_time']
        
        self.logger.info(
            f"索引完成: 处理 {stats['total_files']} 个文件, "
            f"成功 {stats['indexed_files']} 个, "
            f"跳过 {stats['skipped_files']} 个, "
            f"失败 {stats['failed_files']} 个, "
            f"耗时 {stats['duration']:.2f} 秒"
        )
        
        return stats
    
    def _get_changed_files(self, all_files: List[str]) -> List[str]:
        """
        获取需要更新的文件列表（增量更新）
        
        Args:
            all_files: 所有文件路径列表
            
        Returns:
            需要更新的文件列表
        """
        changed_files = []
        
        with self.ix.searcher() as searcher:
            for file_path in all_files:
                # 检查文件是否存在
                if not Path(file_path).exists():
                    continue
                
                # 获取当前文件信息
                metadata = FileMetadata.from_path(file_path)
                if metadata is None:
                    changed_files.append(file_path)
                    continue
                
                # 检查是否已索引
                results = searcher.search(Term('path', metadata.path), limit=1)
                if len(results) == 0:
                    # 新文件
                    changed_files.append(file_path)
                else:
                    # 检查文件是否变化
                    stored_doc = results[0]
                    stored_checksum = stored_doc.get('checksum', '')
                    
                    # 计算当前校验和
                    content = self.parser.parse(file_path) or ""
                    current_checksum = metadata.calculate_checksum(content)
                    
                    if stored_checksum != current_checksum:
                        changed_files.append(file_path)
        
        return changed_files
    
    def search(self, query_str: str, limit: int = 100, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        搜索文件
        
        Args:
            query_str: 搜索查询字符串
            limit: 结果数量限制
            filters: 过滤条件字典
            
        Returns:
            搜索结果列表
        """
        if not self.ix:
            self._open_index()
        
        filters = filters or {}
        results = []
        
        with self.ix.searcher() as searcher:
            # 创建查询解析器
            parser = MultifieldParser(
                ['filename', 'content', 'path', 'extension'],
                schema=self.schema,
                group=OrGroup
            )
            
            # 添加模糊搜索插件
            parser.add_plugin(FuzzyTermPlugin())
            
            # 解析查询
            try:
                query = parser.parse(query_str)
            except Exception as e:
                self.logger.error(f"解析查询失败 '{query_str}': {e}")
                return []
            
            # 应用过滤条件
            if filters:
                filter_queries = []
                
                # 扩展名过滤
                if 'extensions' in filters:
                    ext_terms = [Term('extension', ext) for ext in filters['extensions']]
                    filter_queries.append(Or(ext_terms))
                
                # 文件大小过滤
                if 'min_size' in filters or 'max_size' in filters:
                    min_size = filters.get('min_size', None)
                    max_size = filters.get('max_size', None)
                    filter_queries.append(NumericRange('size', min_size, max_size))
                
                # 修改时间过滤
                if 'modified_after' in filters or 'modified_before' in filters:
                    after = filters.get('modified_after', None)
                    before = filters.get('modified_before', None)
                    filter_queries.append(DateRange('modified', after, before))
                
                # 组合过滤条件
                if filter_queries:
                    filter_query = And(filter_queries)
                    query = And([query, filter_query])
            
            # 执行搜索
            try:
                search_results = searcher.search(query, limit=limit)
                
                for hit in search_results:
                    result = {
                        'path': hit['path'],
                        'filename': hit['filename'],
                        'extension': hit['extension'],
                        'size': hit['size'],
                        'modified': hit['modified'],
                        'created': hit['created'],
                        'content_preview': self._get_content_preview(hit['content']),
                        'score': hit.score,
                        'highlights': hit.highlights('content', top=3) or hit.highlights('filename', top=3),
                    }
                    results.append(result)
                
                self.logger.debug(f"搜索 '{query_str}' 找到 {len(results)} 个结果")
                
            except Exception as e:
                self.logger.error(f"执行搜索失败: {e}")
                return []
        
        return results
    
    def _get_content_preview(self, content: str, max_lines: int = 5, max_chars: int = 200) -> str:
        """获取内容预览"""
        if not content:
            return ""
        
        lines = content.split('\n')
        preview_lines = []
        total_chars = 0
        
        for line in lines[:max_lines]:
            if total_chars + len(line) > max_chars:
                # 截断最后一行
                remaining = max_chars - total_chars
                if remaining > 3:
                    preview_lines.append(line[:remaining] + '...')
                break
            
            preview_lines.append(line)
            total_chars += len(line) + 1  # +1 为换行符
        
        return '\n'.join(preview_lines)
    
    def get_file_count(self) -> int:
        """获取索引中的文件数量"""
        if not self.ix:
            return 0
        
        with self.ix.searcher() as searcher:
            return searcher.doc_count()
    
    def get_index_info(self) -> Dict[str, Any]:
        """获取索引信息"""
        if not self.ix:
            return {}
        
        with self.ix.searcher() as searcher:
            return {
                'doc_count': searcher.doc_count(),
                'index_dir': str(self.index_dir),
                'last_modified': datetime.fromtimestamp(self.index_dir.stat().st_mtime),
                'schema_fields': list(self.schema.names()),
            }
    
    def delete_index(self) -> bool:
        """删除索引"""
        try:
            import shutil
            if self.index_dir.exists():
                shutil.rmtree(self.index_dir)
                self.logger.info(f"删除索引: {self.index_dir}")
                self.ix = None
                return True
        except Exception as e:
            self.logger.error(f"删除索引失败: {e}")
        
        return False
    
    def optimize(self) -> None:
        """优化索引"""
        try:
            self.ix.optimize()
            self.logger.info("索引优化完成")
        except Exception as e:
            self.logger.error(f"索引优化失败: {e}")
    
    def close(self) -> None:
        """关闭索引器"""
        if self.executor:
            self.executor.shutdown(wait=True)
        self.ix = None


# 全局索引器实例
_indexer_instance: Optional[FileIndexer] = None

def get_indexer(index_dir: Optional[str] = None, config=None) -> FileIndexer:
    """获取全局文件索引器"""
    global _indexer_instance
    if _indexer_instance is None:
        if index_dir is None:
            config = config or get_config()
            index_dir = config.index.index_dir
        _indexer_instance = FileIndexer(index_dir, config)
    return _indexer_instance


def close_indexer() -> None:
    """关闭全局索引器"""
    global _indexer_instance
    if _indexer_instance:
        _indexer_instance.close()
        _indexer_instance = None


if __name__ == "__main__":
    # 测试索引器
    config = get_config()
    indexer = FileIndexer(config.index.index_dir, config)
    
    # 测试搜索
    results = indexer.search("test", limit=5)
    print(f"找到 {len(results)} 个结果:")
    for result in results:
        print(f"  - {result['filename']} ({result['path']})")
    
    # 获取索引信息
    info = indexer.get_index_info()
    print(f"\n索引信息: {info}")