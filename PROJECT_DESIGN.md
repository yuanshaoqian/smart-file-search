# Smart File Search - 项目设计方案

## 1. 项目概述
智能本地文件搜索工具，结合了 Everything 的快速文件索引和本地 AI 理解能力，提供图形化交互界面。支持对 Word、Excel、TXT 等文件内容进行索引，通过自然语言查询文件内容和元数据。

## 2. 目录结构
```
smart-file-search/
├── README.md                    # 项目说明
├── requirements.txt             # Python 依赖
├── config.yaml                  # 配置文件
├── start.sh                     # Linux/macOS 启动脚本
├── start.bat                    # Windows 启动脚本
├── src/                         # 源代码
│   ├── main.py                  # 主程序入口
│   ├── config.py                # 配置管理
│   ├── index.py                 # 文件索引模块
│   ├── ai_engine.py             # AI 引擎模块
│   ├── gui.py                   # 图形界面模块
│   └── file_parser.py           # 文件解析器
├── data/                        # 数据存储
│   ├── indexdir/                # Whoosh 索引目录
│   └── models/                  # 本地 AI 模型存储（可选）
├── docs/                        # 文档
│   └── USAGE.md                 # 使用说明
├── logs/                        # 日志文件
└── tests/                       # 单元测试（预留）
```

## 3. 技术栈
- **Python 3.10+**: 主编程语言
- **PyQt6**: 图形用户界面
- **whoosh**: 全文搜索引擎，支持增量索引
- **llama-cpp-python**: 本地 AI 推理，支持 GGUF 模型
- **python-docx**: 读取 Word 文档
- **openpyxl**: 读取 Excel 文件
- **watchdog**: 文件系统监控（未来增量更新）
- **PyYAML**: 配置文件解析
- **loguru**: 日志记录

## 4. 核心模块设计

### 4.1 文件索引模块 (src/index.py)
**功能**:
- 创建/更新 Whoosh 索引，支持增量更新
- 索引文件元数据（名称、路径、大小、修改时间）
- 索引文件内容（TXT、Word、Excel）
- 提供搜索接口，支持模糊匹配和字段过滤

**伪代码**:
```python
class FileIndexer:
    def __init__(self, index_dir):
        self.index_dir = index_dir
        self.schema = Schema(...)  # 定义索引字段
        self.parser = FileParser()
    
    def create_index(self, root_paths):
        # 遍历目录，解析文件，添加至索引
    
    def update_index(self, root_paths):
        # 增量更新：检查文件变化，只更新变更文件
    
    def search(self, query, limit=100, filters=None):
        # 执行搜索，支持多个字段和过滤条件
```

### 4.2 AI 引擎模块 (src/ai_engine.py)
**功能**:
- 加载本地 GGUF 模型（可选）
- 解析用户自然语言问题，转化为结构化查询
- 分析文件内容，提取关键信息
- 提供基于上下文的智能回答

**伪代码**:
```python
class AIEngine:
    def __init__(self, config):
        self.enabled = config.get('ai_enabled', False)
        self.model = None
        if self.enabled:
            self.load_model()
    
    def load_model(self):
        # 加载 llama-cpp-python 模型
    
    def parse_query(self, natural_language):
        # 将自然语言转化为搜索关键词和过滤条件
    
    def generate_answer(self, context_files, question):
        # 基于检索到的文件内容生成回答
```

### 4.3 文件解析器 (src/file_parser.py)
**功能**:
- 统一接口解析多种文件格式
- 提取文本内容，忽略格式
- 处理编码问题

**伪代码**:
```python
class FileParser:
    def parse(self, file_path):
        # 根据扩展名调用相应解析器
        # 支持: .txt, .docx, .xlsx, .pdf (未来)
```

### 4.4 图形界面模块 (src/gui.py)
**功能**:
- PyQt6 主窗口
- 顶部搜索框（支持自然语言）
- 中部 AI 回答显示区域
- 底部文件结果列表（带预览）
- 侧边栏筛选器（文件类型、大小、时间）
- 状态栏显示索引状态

**伪代码**:
```python
class MainWindow(QMainWindow):
    def __init__(self, indexer, ai_engine):
        # 初始化 UI 组件
        self.search_input = QLineEdit()
        self.ai_answer_area = QTextEdit()
        self.result_table = QTableWidget()
        self.filter_panel = QWidget()
    
    def on_search(self):
        # 处理搜索请求，调用索引器和 AI 引擎
```

### 4.5 配置管理 (src/config.py)
**功能**:
- 读取 YAML 配置文件
- 管理应用设置
- 提供默认配置

### 4.6 主程序 (src/main.py)
**功能**:
- 初始化各模块
- 启动 GUI 或 CLI
- 处理命令行参数

## 5. 工作流程
1. **启动应用** → 加载配置 → 初始化索引器（如果索引不存在则创建）
2. **用户输入查询** → 可选通过 AI 引擎解析 → 转换为搜索请求
3. **搜索索引** → 返回匹配的文件列表
4. **如果启用 AI** → 使用检索到的文件内容生成回答
5. **显示结果** → 文件列表 + AI 回答（如果可用）

## 6. 错误处理与日志
- 使用 `loguru` 记录详细日志
- 异常捕获和用户友好的错误提示
- 索引损坏时的恢复机制

## 7. 可扩展性
- 插件式文件解析器
- 支持更多文件格式（PDF, PPT, 图片 OCR 等）
- 支持远程索引（未来）
- 多语言界面

---
*设计完成，接下来将创建具体实现文件。*