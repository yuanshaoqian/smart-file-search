# 🚀 快速配置指南（3步完成）

## 方法1：自动配置（推荐）

```bash
cd ~/smart-file-search
./configure-ai.sh
```

脚本会自动：
- ✅ 检测您的内存大小
- ✅ 推荐最适合的模型
- ✅ 自动下载并配置
- ✅ 优化参数设置

---

## 方法2：手动配置

### 步骤1：选择模型

根据您的内存选择：

| 内存大小 | 推荐模型 | 文件大小 |
|---------|---------|---------|
| **2-4GB** | TinyLlama 1.1B | 0.6GB |
| **2-4GB** | Qwen 0.5B (中文) | 0.4GB |
| **4-8GB** | Phi-2 2.7B ⭐ | 1.6GB |
| **4-8GB** | Qwen 1.8B (中文) | 1.2GB |
| **8GB+** | Mistral 7B | 4.1GB |

### 步骤2：下载模型

```bash
cd ~/smart-file-search/data/models

# 示例：下载 Phi-2（推荐4-8GB内存）
wget -O phi-2.Q4_K_M.gguf \
  https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf
```

### 步骤3：修改配置

编辑 `config.yaml`:

```yaml
ai:
  enabled: true
  model_path: "data/models/phi-2.Q4_K_M.gguf"
  
  # 低内存优化（< 8GB）
  context_size: 1024
  max_tokens: 256
```

---

## 🎯 极低配置方案（< 4GB）

### 方案A：使用微型模型

```yaml
ai:
  enabled: true
  model_path: "data/models/tinyllama-1.1b.Q4_K_M.gguf"
  context_size: 512  # 极小上下文
  max_tokens: 128
```

下载：
```bash
wget -O tinyllama-1.1b.Q4_K_M.gguf \
  https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```

### 方案B：禁用AI（仅索引搜索）

```yaml
ai:
  enabled: false
```

- ✅ 依然可以快速搜索文件
- ✅ 支持文件名、内容、时间筛选
- ❌ 无自然语言理解
- 💾 内存占用 < 100MB

---

## 📊 性能对比

| 配置 | 模型 | 内存占用 | 搜索速度 | AI质量 |
|------|------|---------|---------|--------|
| **无AI** | - | ~100MB | ⚡⚡⚡⚡⚡ | ❌ |
| **极低** | TinyLlama 1.1B | ~1.5GB | ⚡⚡⚡⚡ | ⭐⭐ |
| **低配** | Phi-2 2.7B | ~3GB | ⚡⚡⚡ | ⭐⭐⭐⭐ |
| **中配** | Mistral 7B | ~6GB | ⚡⚡ | ⭐⭐⭐⭐⭐ |

---

## 💡 常见问题

**Q: 我的电脑很卡怎么办？**
```yaml
# 1. 使用更小的模型
ai:
  model_path: "data/models/tinyllama-1.1b.Q4_K_M.gguf"
  context_size: 512

# 2. 减少索引范围
index:
  directories:
    - "~/Documents"  # 只索引文档目录
  
# 3. 降低并发
advanced:
  parser_threads: 1
  indexer_threads: 1
```

**Q: 如何查看当前内存占用？**

启动程序后，GUI右下角会显示：
```
AI状态: 已启用
模型: Phi-2 2.7B
内存: 2.8 GB / 8.0 GB
```

**Q: 可以先用索引搜索，之后再启用AI吗？**

可以！随时修改 `config.yaml`:
```yaml
ai:
  enabled: true  # 改为 true
```
然后重启程序即可。

---

## 🔄 切换模型

```bash
# 重新运行配置脚本
./configure-ai.sh

# 或手动修改 config.yaml 中的 model_path
```

---

## 📚 更多信息

- **详细指南**: `docs/LOW_SPEC_GUIDE.md`
- **使用说明**: `docs/USAGE.md`
- **技术设计**: `PROJECT_DESIGN.md`

---

**推荐**:
- 4-8GB 内存 → **Phi-2 2.7B** （质量和速度的最佳平衡）
- 中文用户 → **Qwen 1.8B** （中文支持更好）
- 极低配置 → **TinyLlama 1.1B** 或禁用AI
