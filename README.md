# Smart File Search - 智能本地文件搜索工具

一个结合了 Everything 快速文件索引和本地 AI 理解能力的图形化文件搜索工具。支持对 Word、Excel、TXT 等文件内容进行索引，并通过自然语言查询文件内容和元数据。

## 功能特性

### 🚀 快速文件索引
- **闪电搜索**：基于 Whoosh 全文搜索引擎，毫秒级响应
- **增量更新**：只索引变更文件，节省系统资源
- **多格式支持**：支持 TXT、Word (.docx)、Excel (.xlsx) 文件内容索引
- **元数据索引**：文件名、路径、大小、修改时间、文件类型

### 🤖 本地 AI 理解
- **自然语言查询**：用日常语言描述你要找的文件
- **智能解析**：AI 引擎将自然语言转化为结构化搜索条件
- **上下文理解**：基于文件内容生成精准回答
- **完全本地**：使用 llama.cpp 运行 GGUF 模型，隐私安全

### 🎨 现代化 GUI
- **直观界面**：PyQt6 构建的现代化桌面应用
- **三栏布局**：
  - 顶部：搜索框（支持自然语言）
  - 中部：AI 回答区域
  - 底部：文件结果列表（带预览）
- **侧边筛选**：按文件类型、大小、时间筛选结果
- **实时预览**：点击文件查看内容摘要

### 🔧 高级功能
- **模糊匹配**：支持通配符和近似匹配
- **组合搜索**：`size>1MB modified:today content:report`
- **批量操作**：支持批量打开、复制路径
- **配置灵活**：YAML 配置文件，可自定义索引路径、AI 模型等

## 快速开始

### 系统要求
- Python 3.10+
- 至少 4GB RAM（启用 AI 需要额外内存）
- 磁盘空间：索引约占原文件大小的 5-10%

### 安装步骤

1. **克隆/下载项目**
   ```bash
   cd ~
   git clone <repository-url> smart-file-search
   cd smart-file-search
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置应用**
   ```bash
   # 编辑 config.yaml 设置索引路径等
   cp config.yaml.example config.yaml
   ```

4. **首次运行（创建索引）**
   ```bash
   # Linux/macOS
   ./start.sh --init
   
   # Windows
   start.bat --init
   ```

5. **正常使用**
   ```bash
   ./start.sh
   ```

### 配置说明

主要配置选项（`config.yaml`）：
```yaml
# 索引配置
index:
  directories:
    - ~/Documents
    - ~/Downloads
  exclude_patterns:
    - "*.tmp"
    - "*.log"
  update_interval: 300  # 自动更新间隔（秒）

# AI 配置
ai:
  enabled: false  # 是否启用 AI 功能
  model_path: ~/models/llama-2-7b.Q4_K_M.gguf
  context_size: 2048

# GUI 配置
gui:
  theme: "dark"  # dark/light
  font_size: 12
  max_results: 500
```

## 使用示例

### 基础搜索
- `财务报告` → 搜索文件名或内容包含"财务报告"的文件
- `*.pdf modified:lastweek` → 上周修改过的 PDF 文件
- `size>10MB` → 大于 10MB 的文件

### 自然语言搜索（需要启用 AI）
- `帮我找一下上个月写的项目总结文档` → AI 解析为时间、内容关键词
- `小张发给我的 Excel 表格` → 结合文件名、内容、元数据综合搜索
- `关于机器学习的论文` → 从文档内容中识别主题

### AI 问答
- 问：`这些文件中哪些提到了预算？`
- AI 回答：`在以下 3 个文件中提到了预算：1. 2024预算.xlsx（第5-8行）...`

## 项目结构

```
smart-file-search/
├── src/                    # 源代码
│   ├── main.py            # 主程序入口
│   ├── config.py          # 配置管理
│   ├── index.py           # 文件索引模块
│   ├── ai_engine.py       # AI 引擎模块
│   ├── gui.py             # 图形界面
│   └── file_parser.py     # 文件解析器
├── data/                  # 数据存储
│   ├── indexdir/          # Whoosh 索引目录
│   └── models/            # 本地 AI 模型
├── docs/                  # 文档
├── logs/                  # 日志文件
└── tests/                 # 单元测试
```

## 技术栈

- **Python 3.10+** - 主编程语言
- **PyQt6** - 图形用户界面
- **whoosh** - 全文搜索引擎
- **llama-cpp-python** - 本地 AI 推理
- **python-docx** - Word 文档解析
- **openpyxl** - Excel 文件解析
- **watchdog** - 文件系统监控
- **PyYAML** - 配置文件解析
- **loguru** - 日志记录

## 开发指南

### 运行开发环境
```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
pytest tests/

# 启动开发版本
python src/main.py --debug
```

### 添加新文件格式支持
1. 在 `file_parser.py` 中添加新的解析器类
2. 实现 `parse()` 方法返回纯文本
3. 在 `FileParser` 类中注册新的扩展名

### 扩展 AI 功能
1. 在 `ai_engine.py` 中修改提示词模板
2. 调整搜索查询生成逻辑
3. 添加新的模型支持

## 常见问题

### Q: 索引占用多少磁盘空间？
A: 通常为原文件大小的 5-10%，仅文本内容被索引。

### Q: AI 功能必须启用吗？
A: 不是必须的。AI 功能是可选的，即使禁用也能使用传统搜索。

### Q: 支持中文搜索吗？
A: 是的，Whoosh 支持中文分词，AI 模型也支持中文。

### Q: 如何添加新的索引目录？
A: 编辑 `config.yaml` 中的 `index.directories` 列表，然后重新索引。

### Q: 索引更新是实时的吗？
A: 默认每 5 分钟检查一次更新，也可手动触发立即更新。

## 路线图

- [ ] 支持 PDF 文件解析
- [ ] 图片 OCR 文字提取
- [ ] 云端同步索引
- [ ] 移动端应用
- [ ] 插件系统
- [ ] 多语言界面

## 许可证

MIT License - 详见 LICENSE 文件。

## 贡献

欢迎提交 Issue 和 Pull Request！请确保代码符合 PEP 8 规范并包含适当的测试。

## 支持

如有问题，请：
1. 查看 [docs/USAGE.md](docs/USAGE.md) 详细使用说明
2. 检查 [issues](https://github.com/yourusername/smart-file-search/issues)
3. 提交新的 Issue 并包含系统信息和错误日志