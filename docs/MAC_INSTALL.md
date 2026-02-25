# Mac 安装指南

## ⚠️ Mac 特殊说明

Mac 上安装 `llama-cpp-python` 需要编译，可能遇到问题。以下是解决方案。

---

## 🚀 快速开始（3种方式）

### 方式1：跳过AI功能（最快）⭐ 推荐

```bash
# 1. 安装基础依赖（不含AI）
pip install -r requirements-mac.txt

# 2. 禁用AI功能
# 编辑 config.yaml:
ai:
  enabled: false

# 3. 启动程序
./start.sh
```

**优点：** 立即可用，快速搜索功能正常
**缺点：** 无自然语言理解

---

### 方式2：使用预编译包（推荐）

```bash
# 安装预编译版本
pip install llama-cpp-python \
  --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu

# 如果失败，尝试Metal版本（Mac专用）
pip install llama-cpp-python \
  --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/metal
```

**优点：** 无需编译，安装快速
**缺点：** 可能版本较旧

---

### 方式3：安装编译依赖

```bash
# 1. 安装Xcode命令行工具
xcode-select --install

# 2. 安装Homebrew（如未安装）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 3. 安装依赖
brew install cmake libomp

# 4. 安装llama-cpp-python
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --no-cache-dir
```

**优点：** 支持Mac Metal加速，性能最佳
**缺点：** 编译耗时（10-20分钟）

---

## 📋 详细步骤

### 步骤1：解压项目

```bash
# 解压
tar -xzf SmartFileSearch-v1.0.0-full.tar.gz

# 进入目录
cd SmartFileSearch-v1.0.0-full
```

### 步骤2：安装依赖

**选择A：不使用AI（推荐新手）**
```bash
pip install -r requirements-mac.txt
```

**选择B：使用预编译AI包**
```bash
# 先安装基础依赖
pip install -r requirements-mac.txt

# 再安装预编译的AI包
pip install llama-cpp-python \
  --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/metal
```

**选择C：从源码编译（高级用户）**
```bash
# 安装编译工具
brew install cmake libomp

# 编译安装
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --no-cache-dir
```

### 步骤3：配置AI（如已安装）

```bash
# 编辑配置文件
nano config.yaml

# 修改以下内容
ai:
  enabled: true
  model_path: "data/models/phi-2.Q4_K_M.gguf"
```

### 步骤4：启动程序

```bash
./start.sh
```

---

## 🎯 Mac 性能优化

### Metal 加速（Mac专用）

如果您从源码编译，建议启用Metal加速：

```bash
# 启用Metal支持
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --no-cache-dir --force-reinstall --upgrade
```

### 配置优化

编辑 `config.yaml`:

```yaml
ai:
  enabled: true
  model_path: "data/models/phi-2.Q4_K_M.gguf"

  # Mac 优化配置
  context_size: 1024      # 降低内存占用
  max_tokens: 256
  temperature: 0.1

  # Metal 加速（需重新编译）
  n_gpu_layers: 1  # 使用GPU加速
```

---

## ⚠️ 常见问题

### Q: 提示"command not found: xcode-select"

A: 打开终端，运行：
```bash
xcode-select --install
```

### Q: brew install 很慢

A: 使用国内镜像：
```bash
# 清华镜像
export HOMEBREW_BREW_GIT_REMOTE="https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/brew.git"
export HOMEBREW_CORE_GIT_REMOTE="https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/homebrew-core.git"
```

### Q: 编译时内存不足

A: 关闭其他应用，或使用预编译包

### Q: Metal不可用

A: 检查Mac型号是否支持Metal：
- MacBook Pro (2012及以后)
- MacBook Air (2012及以后)
- Mac mini (2012及以后)
- iMac (2012及以后)

### Q: 还是失败怎么办？

A: 使用方式1（跳过AI功能），或使用conda：
```bash
# 安装miniconda
brew install --cask miniconda

# 创建环境
conda create -n smartsearch python=3.10
conda activate smartsearch

# 安装llama-cpp-python
conda install -c conda-forge llama-cpp-python
```

---

## 🎁 快速测试

安装完成后测试：

```bash
# 测试基础功能
python -c "import PyQt6; print('GUI OK')"
python -c "import whoosh; print('Search OK')"

# 测试AI功能（如已安装）
python -c "import llama_cpp; print('AI OK')"
```

---

## 📊 性能对比

| Mac型号 | AI状态 | 搜索速度 | AI响应速度 |
|---------|--------|---------|-----------|
| M1/M2/M3 | Metal加速 | 极快 | 快（2-3秒） |
| Intel Mac | CPU | 快 | 中等（5-8秒） |
| 任意Mac | 禁用AI | 极快 | ❌ |

---

## 💡 建议

**新手用户：**
1. 使用方式1（跳过AI）
2. 先体验快速搜索功能
3. 熟悉后再尝试安装AI

**高级用户：**
1. 安装编译依赖
2. 启用Metal加速
3. 享受最佳性能

**M1/M2/M3 Mac：**
1. 强烈建议编译安装
2. 启用Metal加速
3. 性能提升3-5倍

---

## 📞 需要帮助？

如果仍有问题：
1. 查看错误日志
2. 尝试不同方式
3. 或暂时禁用AI功能

---

**总结：**
- ✅ Mac可以正常运行
- ✅ 建议先跳过AI功能快速开始
- ✅ 高级用户可编译启用Metal加速
- ✅ M系列芯片性能最佳
