# 微型模型推荐指南
# 适用于低配置电脑（4GB-8GB RAM）

## 🎯 推荐的微型模型

### ⭐ 超微型模型（2GB以下）- **强烈推荐低配置电脑**

1. **Phi-2 (2.7B Q4)**
   - **文件大小**: ~1.6 GB
   - **内存需求**: 2-3 GB RAM
   - **下载**:
     ```bash
     cd ~/smart-file-search/data/models
     wget -O phi-2.Q4_K_M.gguf \
       https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf
     ```
   - **配置**:
     ```yaml
     ai:
       enabled: true
       model_path: "data/models/phi-2.Q4_K_M.gguf"
       context_size: 1024  # 降低上下文长度
       max_tokens: 256
     ```
   - **特点**: 微软出品，质量优秀，速度极快

2. **TinyLlama (1.1B Q4)**
   - **文件大小**: ~0.6 GB
   - **内存需求**: 1-2 GB RAM
   - **下载**:
     ```bash
     wget -O tinyllama-1.1b.Q4_K_M.gguf \
       https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
     ```
   - **配置**:
     ```yaml
     ai:
       enabled: true
       model_path: "data/models/tinyllama-1.1b.Q4_K_M.gguf"
       context_size: 1024
       max_tokens: 256
     ```
   - **特点**: 超轻量级，极快速度

3. **Qwen 1.5 0.5B (中文优化)**
   - **文件大小**: ~0.4 GB
   - **内存需求**: 1 GB RAM
   - **下载**:
     ```bash
     wget -O qwen-0.5b.Q4_K_M.gguf \
       https://huggingface.co/Qwen/Qwen1.5-0.5B-Chat-GGUF/resolve/main/qwen1.5-0.5b-chat.Q4_K_M.gguf
     ```
   - **配置**:
     ```yaml
     ai:
       enabled: true
       model_path: "data/models/qwen-0.5b.Q4_K_M.gguf"
       context_size: 1024
       max_tokens: 256
     ```
   - **特点**: 中文支持最佳，极小体积

### 💪 小型模型（2-4GB）- 推荐

1. **Mistral 7B Q4 (推荐)**
   - **文件大小**: ~4.1 GB
   - **内存需求**: 5-6 GB RAM
   - **下载**:
     ```bash
     wget -O mistral-7b.Q4_K_M.gguf \
       https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf
     ```
   - **特点**: 质量高，速度快

2. **Qwen 1.5 1.8B (中文)**
   - **文件大小**: ~1.2 GB
   - **内存需求**: 2-3 GB RAM
   - **下载**:
     ```bash
     wget -O qwen-1.8b.Q4_K_M.gguf \
       https://huggingface.co/Qwen/Qwen1.5-1.8B-Chat-GGUF/resolve/main/qwen1.5-1.8b-chat.Q4_K_M.gguf
     ```
   - **特点**: 中文支持好，体积小

## 🔧 低配置电脑优化建议

### 配置优化（config.yaml）

```yaml
# AI 配置优化
ai:
  enabled: true
  model_path: "data/models/phi-2.Q4_K_M.gguf"  # 使用微型模型
  
  # 降低上下文长度（减少内存占用）
  context_size: 1024  # 默认2048，低配建议512-1024
  
  # 减少生成长度
  max_tokens: 256  # 默认512，低配建议128-256
  
  # 降低温度（提高确定性，减少计算）
  temperature: 0.1

# 索引优化
index:
  # 减少并发线程数
  max_file_size: 52428800  # 50MB（默认100MB）
  
  # 减少索引频率
  update_interval: 600  # 10分钟（默认5分钟）

# GUI 优化
gui:
  # 减少结果显示数量
  max_results: 200  # 默认500
  
  # 禁用预览（可选）
  preview_max_lines: 10  # 默认20

# 高级优化
advanced:
  # 减少线程数
  parser_threads: 2  # 默认4
  indexer_threads: 1  # 默认2
  
  # 减少缓存
  cache_size_mb: 50  # 默认100
```

### 内存优化技巧

1. **使用更低的量化版本**
   - Q4_K_M (推荐): 质量与速度平衡
   - Q4_K_S: 更小体积，略低质量
   - Q3_K_M: 最小体积，质量较低

2. **调整上下文长度**
   ```yaml
   context_size: 512  # 极低内存（<4GB）
   context_size: 1024  # 低内存（4-6GB）
   context_size: 2048  # 中等内存（8GB+）
   ```

3. **禁用AI功能（仅使用索引）**
   ```yaml
   ai:
     enabled: false  # 纯索引搜索，无AI理解
   ```

## 💻 不同配置推荐

### 极低配置（2-4GB RAM）
- **模型**: TinyLlama 1.1B 或 Qwen 0.5B
- **配置**:
  ```yaml
  ai:
    enabled: true
    model_path: "data/models/tinyllama-1.1b.Q4_K_M.gguf"
    context_size: 512
    max_tokens: 128
  ```

### 低配置（4-6GB RAM）
- **模型**: Phi-2 2.7B 或 Qwen 1.8B
- **配置**:
  ```yaml
  ai:
    enabled: true
    model_path: "data/models/phi-2.Q4_K_M.gguf"
    context_size: 1024
    max_tokens: 256
  ```

### 中等配置（8-12GB RAM）
- **模型**: Mistral 7B 或 Qwen 7B
- **配置**:
  ```yaml
  ai:
    enabled: true
    model_path: "data/models/mistral-7b.Q4_K_M.gguf"
    context_size: 2048
    max_tokens: 512
  ```

### 高配置（16GB+ RAM）
- **模型**: Llama 2 13B 或更大
- **配置**: 使用默认配置即可

## 🚀 快速开始（低配版）

```bash
# 1. 创建模型目录
cd ~/smart-file-search
mkdir -p data/models

# 2. 下载 Phi-2（推荐低配）
cd data/models
wget -O phi-2.Q4_K_M.gguf \
  https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf

# 3. 修改配置
cd ~/smart-file-search
nano config.yaml
# 修改 ai.enabled: true
# 修改 ai.model_path: "data/models/phi-2.Q4_K_M.gguf"
# 修改 ai.context_size: 1024
# 修改 ai.max_tokens: 256

# 4. 安装AI依赖
pip install llama-cpp-python

# 5. 启动程序
./start.sh
```

## ⚡ 性能对比

| 模型 | 大小 | 内存 | 速度 | 质量 | 适用场景 |
|------|------|------|------|------|---------|
| TinyLlama 1.1B | 0.6GB | 1-2GB | ⚡⚡⚡⚡⚡ | ⭐⭐ | 极低配置 |
| Qwen 0.5B | 0.4GB | 1GB | ⚡⚡⚡⚡⚡ | ⭐⭐ | 中文极低配 |
| Phi-2 2.7B | 1.6GB | 2-3GB | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | 低配置推荐 |
| Qwen 1.8B | 1.2GB | 2-3GB | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | 中文低配 |
| Mistral 7B | 4.1GB | 5-6GB | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | 中配置 |
| Llama 2 7B | 4.0GB | 6GB | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | 中配置 |

## 🔍 常见问题

**Q: 我的电脑只有4GB内存，能用吗？**
A: 可以！使用 TinyLlama 1.1B 或 Qwen 0.5B，设置 context_size=512

**Q: 不想用AI，只想快速搜索文件？**
A: 设置 `ai.enabled: false`，仅使用索引功能（类似Everything）

**Q: 如何查看内存占用？**
A: 启动程序后，侧边栏会显示"AI状态"和内存占用

**Q: 模型加载失败？**
A: 检查模型文件是否完整下载，路径是否正确

## 📚 资源链接

- **Hugging Face GGUF 模型库**: https://huggingface.co/models?search=gguf
- **llama.cpp 文档**: https://github.com/ggerganov/llama.cpp
- **量化说明**: https://github.com/ggerganov/llama.cpp#quantization

---

**推荐**: 低配置电脑首选 **Phi-2 2.7B** 或 **Qwen 1.8B**，平衡性能和质量！
