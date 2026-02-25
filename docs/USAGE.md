# Smart File Search 使用说明

## 目录

1. [快速入门](#快速入门)
2. [安装配置](#安装配置)
3. [图形界面使用](#图形界面使用)
4. [命令行使用](#命令行使用)
5. [AI 功能](#ai-功能)
6. [高级配置](#高级配置)
7. [常见问题](#常见问题)
8. [故障排除](#故障排除)

---

## 快速入门

### 第一次使用

1. **安装依赖**
   ```bash
   cd ~/smart-file-search
   pip install -r requirements.txt
   ```

2. **初始化索引**
   ```bash
   ./start.sh --init
   ```
   
   或 Windows:
   ```cmd
   start.bat --init
   ```

3. **启动应用**
   ```bash
   ./start.sh
   ```

4. **开始搜索**
   - 在搜索框输入关键词
   - 按 Enter 或点击"搜索"按钮
   - 查看结果列表和 AI 回答

---

## 安装配置

### 系统要求

- **操作系统**: Windows 10+, macOS 10.14+, Linux (Ubuntu 20.04+)
- **Python**: 3.10 或更高版本
- **内存**: 至少 4GB RAM（启用 AI 需要额外 2-4GB）
- **磁盘**: 索引约占原文件大小的 5-10%

### 依赖安装

**基础依赖（必需）**:
```bash
pip install PyQt6 whoosh python-docx openpyxl PyYAML loguru watchdog chardet
```

**AI 功能依赖（可选）**:
```bash
pip install llama-cpp-python
```

> **注意**: 在某些系统上，`llama-cpp-python` 可能需要编译。请参考 [llama-cpp-python 文档](https://github.com/abetlen/llama-cpp-python)。

### 配置文件

配置文件位于 `config.yaml`，主要配置项：

```yaml
# 索引目录
index:
  directories:
    - ~/Documents
    - ~/Downloads
    - ~/Desktop
  
  # 排除文件
  exclude_patterns:
    - "*.tmp"
    - "*.log"
    - ".git"
  
  # 文件大小限制
  max_file_size: 104857600  # 100MB

# AI 设置
ai:
  enabled: false
  model_path: "data/models/llama-2-7b.Q4_K_M.gguf"
  context_size: 2048

# 界面设置
gui:
  theme: "dark"
  font_size: 12
  max_results: 500
```

---

## 图形界面使用

### 主界面布局

```
┌─────────────────────────────────────────────────────────┐
│  [搜索框...................................] [搜索] [AI] │
├────────────┬────────────────────────────────────────────┤
│            │  🤖 AI 智能回答                           │
│  筛选条件  │  ────────────────────────────────────────  │
│            │  AI 回答显示在这里...                     │
│  文件类型  │                                            │
│  ○ 全部    ├────────────────────────────────────────────┤
│  ○ 文档    │  搜索结果                                  │
│  ○ 表格    │  ───────┬─────────┬─────┬────────┬─────── │
│            │  文件名 │ 路径    │ 大小│ 修改   │ 匹配度 │
│  文件大小  │  ───────┼─────────┼─────┼────────┼─────── │
│  最小: 0   │  test   │ /tmp/.. │ 1MB │ 01-15  │ 0.95  │
│  最大: 不限│                                          │
│            │                                            │
│  修改时间  │  共 25 个结果                              │
│  从:       ├────────────────────────────────────────────┤
│  到:       │  状态: 就绪    索引: 1234 个文件  AI: 启用 │
└────────────┴────────────────────────────────────────────┘
```

### 搜索功能

#### 1. 基础搜索

在搜索框输入关键词，按 Enter 执行搜索：

- `报告` - 搜索文件名或内容包含"报告"的文件
- `财务报表 2024` - 搜索包含"财务报表"和"2024"的文件
- `*.pdf` - 搜索所有 PDF 文件

#### 2. 高级搜索语法

支持多种搜索语法：

| 语法 | 示例 | 说明 |
|------|------|------|
| 通配符 | `*.pdf` | 匹配所有 PDF 文件 |
| 短语 | `"年度报告"` | 精确匹配短语 |
| OR | `报告 OR 总结` | 匹配任一关键词 |
| NOT | `报告 NOT 草稿` | 排除包含"草稿"的文件 |
| 模糊 | `报告~2` | 允许 2 个字符的编辑距离 |

#### 3. 筛选器使用

**文件类型筛选**:
- 全部：不限制文件类型
- 文档：`.docx`, `.doc`
- 表格：`.xlsx`, `.xls`
- 文本：`.txt`, `.md`
- 代码：`.py`, `.java`, `.cpp`

**文件大小筛选**:
1. 勾选"启用大小筛选"
2. 设置最小/最大文件大小
3. 0 表示不限制

**修改时间筛选**:
1. 勾选"启用时间筛选"
2. 选择日期范围
3. 使用日历选择具体日期

### 结果操作

- **双击文件**: 在默认应用中打开
- **右键菜单**:
  - 打开文件
  - 打开所在文件夹
  - 复制文件路径
  - 查看属性

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+F` | 聚焦搜索框 |
| `Enter` | 执行搜索 |
| `Escape` | 清空搜索 |
| `F3` | 下一个结果 |
| `Shift+F3` | 上一个结果 |
| `Ctrl+O` | 打开选中文件 |
| `Ctrl+D` | 打开所在文件夹 |
| `Ctrl+C` | 复制文件路径 |
| `F5` | 更新索引 |

---

## 命令行使用

### 基本命令

```bash
# 启动图形界面
python src/main.py

# 初始化索引
python src/main.py --init

# 增量更新索引
python src/main.py --update

# 命令行搜索
python src/main.py --search "报告"

# AI 搜索
python src/main.py --ai "上周修改的PDF文档"

# 调试模式
python src/main.py --debug

# 指定配置文件
python src/main.py --config /path/to/config.yaml
```

### 使用启动脚本

**Linux/macOS**:
```bash
# 正常启动
./start.sh

# 初始化索引
./start.sh --init

# 调试模式
./start.sh --debug
```

**Windows**:
```cmd
# 正常启动
start.bat

# 初始化索引
start.bat --init

# 调试模式
start.bat --debug
```

---

## AI 功能

### 启用 AI

1. **下载模型**

   从 Hugging Face 下载 GGUF 格式模型：
   
   ```bash
   cd ~/smart-file-search
   mkdir -p data/models
   
   # 示例：下载 Llama 2 7B (Q4 量化)
   wget -O data/models/llama-2-7b.Q4_K_M.gguf \
     https://huggingface.co/TheBloke/Llama-2-7B-GGUF/resolve/main/llama-2-7b.Q4_K_M.gguf
   ```

2. **修改配置**

   编辑 `config.yaml`:
   ```yaml
   ai:
     enabled: true
     model_path: "data/models/llama-2-7b.Q4_K_M.gguf"
   ```

3. **重启应用**

### AI 搜索示例

使用自然语言描述你要找的文件：

- "帮我找一下上个月写的项目总结"
- "2024年的财务报表在哪里"
- "小张发给我的Excel表格"
- "关于机器学习的论文或文档"
- "最近修改的配置文件"

### AI 工作原理

1. **意图分析**: AI 解析自然语言，提取关键词和过滤条件
2. **智能搜索**: 将意图转化为结构化搜索查询
3. **上下文理解**: 分析搜索到的文件内容
4. **生成回答**: 基于文件内容生成精准回答

### 支持的 AI 模型

推荐使用以下 GGUF 格式模型：

| 模型 | 大小 | 内存需求 | 说明 |
|------|------|----------|------|
| Llama 2 7B Q4 | ~4GB | 6GB | 平衡性能和质量 |
| Llama 2 13B Q4 | ~8GB | 10GB | 更高质量 |
| Mistral 7B Q4 | ~4GB | 6GB | 速度快 |
| Qwen 7B Q4 | ~4GB | 6GB | 中文支持好 |

---

## 高级配置

### 索引优化

**增量更新配置**:
```yaml
index:
  incremental: true
  update_interval: 300  # 每 5 分钟自动检查更新
```

**排除规则**:
```yaml
index:
  exclude_patterns:
    - "*.tmp"
    - "*.log"
    - "*.cache"
    - ".git"
    - ".svn"
    - "node_modules"
    - "__pycache__"
```

### 性能调优

**多线程配置**:
```yaml
advanced:
  parser_threads: 4     # 文件解析线程数
  indexer_threads: 2    # 索引写入线程数
  cache_size_mb: 100    # 缓存大小
```

**AI 性能**:
```yaml
ai:
  context_size: 2048    # 上下文长度
  max_tokens: 512       # 最大生成 token 数
  temperature: 0.1      # 降低随机性
```

### 自定义文件类型

添加更多支持的文件扩展名：
```yaml
index:
  supported_extensions:
    - ".txt"
    - ".md"
    - ".py"
    - ".java"
    - ".go"
    - ".rs"
    - ".docx"
    - ".xlsx"
    # 添加更多...
```

---

## 常见问题

### Q: 索引创建很慢怎么办？

A: 
1. 减少索引目录数量
2. 添加更多排除规则
3. 增加解析线程数
4. 使用增量更新而非全量重建

### Q: 搜索结果不准确？

A: 
1. 尝试更精确的关键词
2. 使用引号进行短语搜索
3. 启用模糊搜索
4. 检查筛选条件是否正确

### Q: AI 功能无法使用？

A: 
1. 确认已安装 `llama-cpp-python`
2. 检查模型文件是否存在
3. 确认配置中 `ai.enabled: true`
4. 查看日志文件中的错误信息

### Q: 如何处理中文文件？

A: 
1. 确保系统编码为 UTF-8
2. 使用中文关键词搜索
3. 选择支持中文的 AI 模型（如 Qwen）

### Q: 内存占用过高？

A: 
1. 减小 AI 模型的上下文长度
2. 使用更小的量化模型
3. 减少缓存大小
4. 限制最大搜索结果数

---

## 故障排除

### 查看日志

日志文件位于 `logs/app.log`：
```bash
# 查看最新日志
tail -f logs/app.log

# 搜索错误
grep ERROR logs/app.log
```

### 重建索引

如果索引损坏：
```bash
# 删除旧索引
rm -rf data/indexdir/*

# 重新创建
./start.sh --init
```

### 重置配置

恢复默认配置：
```bash
# 备份当前配置
cp config.yaml config.yaml.backup

# 删除配置文件，重启会自动创建默认配置
rm config.yaml
./start.sh
```

### 调试模式

启用详细日志：
```bash
./start.sh --debug
```

### 报告问题

如果遇到问题，请提供以下信息：
1. 操作系统版本
2. Python 版本 (`python --version`)
3. 错误信息（从日志文件复制）
4. 复现步骤

---

## 更新日志

### v1.0.0 (2024-01-01)
- 初始版本发布
- 支持 Word、Excel、TXT 文件索引
- AI 自然语言搜索
- PyQt6 图形界面
- 增量索引更新

---

## 技术支持

- **文档**: [docs/](./)
- **问题反馈**: GitHub Issues
- **社区讨论**: GitHub Discussions

---

*最后更新: 2024-01-01*