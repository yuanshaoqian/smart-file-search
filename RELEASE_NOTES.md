# Smart File Search v1.0.0 - 完整版发布包

## 📦 文件信息

- **文件名**: SmartFileSearch-v1.0.0-full.tar.gz
- **大小**: 1.7 GB
- **MD5**: 2d0675660dfa543ec608209771df5749
- **发布日期**: 2026-02-24

## 📋 包含内容

### ✅ 完整功能
- **源代码** (src/)
  - 文件索引引擎
  - AI理解模块
  - PyQt6图形界面
  - 文件解析器

- **AI模型** (data/models/)
  - Phi-2 2.7B Q4 (1.7GB)
  - 上下文长度: 2048 tokens
  - 内存需求: ~3GB RAM

- **文档** (docs/)
  - 使用说明 (USAGE.md)
  - 低配优化指南 (LOW_SPEC_GUIDE.md)
  - 快速配置 (QUICK_SETUP.md)

- **配置文件**
  - config.yaml (已配置AI)
  - requirements.txt (依赖清单)

- **启动脚本**
  - start.sh (Linux/macOS)
  - start.bat (Windows)
  - install.bat (Windows快速安装)

## 🚀 快速开始

### Windows用户

1. **解压文件**
   ```
   使用 7-Zip 或 WinRAR 解压
   ```

2. **安装依赖**
   ```
   双击运行 install.bat
   ```

3. **启动程序**
   ```
   双击 start.bat
   或使用桌面快捷方式
   ```

### Linux/macOS用户

1. **解压文件**
   ```bash
   tar -xzf SmartFileSearch-v1.0.0-full.tar.gz
   cd SmartFileSearch-v1.0.0-full
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **启动程序**
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

## ⚙️ 系统要求

### 最低配置
- **CPU**: 双核处理器
- **内存**: 4GB RAM（8GB推荐）
- **磁盘**: 5GB可用空间
- **系统**: Windows 10+ / macOS 10.14+ / Linux
- **Python**: 3.10或更高版本

### 推荐配置
- **CPU**: 四核处理器
- **内存**: 8GB+ RAM
- **磁盘**: 10GB可用空间

## 🎯 主要功能

### 1. 快速文件搜索
- ⚡ 毫秒级响应（类似Everything）
- 🔍 按文件名、内容、时间、大小检索
- 🎯 支持模糊匹配和通配符

### 2. AI智能理解
- 🤖 自然语言查询
- 💡 智能文件内容分析
- 📊 精准结果生成
- 🔒 完全本地运行（无网络传输）

### 3. 支持的文件格式
- 📄 Word文档 (.docx)
- 📊 Excel表格 (.xlsx)
- 📝 文本文件 (.txt)
- 📋 Markdown文件 (.md)
- 💻 代码文件 (.py, .java, .cpp等)

## 💡 使用示例

### 基础搜索
```
关键词: 项目报告
时间范围: 上周
文件类型: Word
```

### AI自然语言查询
```
"帮我找一下上个月写的销售报表"
"2024年的财务Excel文件在哪里"
"包含客户联系方式的文档"
"最近修改的配置文件"
```

## 🔧 配置说明

### AI功能（已启用）
默认配置适合8GB+内存：
```yaml
ai:
  enabled: true
  model_path: "data/models/phi-2.Q4_K_M.gguf"
  context_size: 2048
  max_tokens: 512
```

### 低内存优化（< 6GB）
编辑 `config.yaml`:
```yaml
ai:
  context_size: 1024  # 降低上下文
  max_tokens: 256     # 减少生成长度
```

### 禁用AI（仅索引搜索）
```yaml
ai:
  enabled: false
```

## 📚 文档位置

- **完整使用说明**: `docs/USAGE.md`
- **低配优化指南**: `docs/LOW_SPEC_GUIDE.md`
- **快速配置**: `docs/QUICK_SETUP.md`
- **项目设计**: `PROJECT_DESIGN.md`

## ⚠️ 注意事项

1. **首次启动**
   - 会自动创建文件索引
   - 根据文件数量，可能需要几分钟
   - 建议先索引文档目录

2. **AI模型加载**
   - 首次启动AI需要10-30秒加载模型
   - 加载后会常驻内存（约3GB）
   - 可在配置中禁用AI以节省内存

3. **文件索引**
   - 默认索引: ~/Documents, ~/Downloads, ~/Desktop
   - 可在 config.yaml 中修改索引路径
   - 支持增量更新（仅索引变更文件）

## 🐛 故障排除

### 问题1: Python未找到
**解决**: 安装 Python 3.10+ 并添加到PATH

### 问题2: 依赖安装失败
**解决**:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 问题3: AI模型加载失败
**解决**:
- 检查 data/models/phi-2.Q4_K_M.gguf 是否存在
- 检查文件大小是否为1.7GB
- 确保有足够内存（至少4GB空闲）

### 问题4: 内存不足
**解决**:
- 降低 context_size 到 1024 或 512
- 禁用AI功能（ai.enabled: false）

## 📞 技术支持

- **问题反馈**: (GitHub Issues链接)
- **邮箱支持**: (邮箱地址)
- **文档中心**: docs/目录

## 📜 许可证

本项目仅供学习和个人使用。

---

**感谢使用 Smart File Search！** 🎉
