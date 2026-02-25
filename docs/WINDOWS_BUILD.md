# Windows 安装包生成指南

## 📦 从 tar.gz 到 exe 安装包

由于当前环境是 Linux，无法直接生成 Windows .exe 文件。但所有配置已准备好，您只需在 Windows 上执行简单步骤即可。

---

## 🚀 快速开始（3步）

### 步骤1：传输文件到 Windows

将 `SmartFileSearch-v1.0.0-full.tar.gz` 传输到 Windows 电脑：
- 使用 U盘
- 网络共享（SMB）
- 或分卷压缩后传输

### 步骤2：解压

在 Windows 上使用 7-Zip 或 WinRAR 解压：
```
右键 → 7-Zip → 解压到当前文件夹
```

### 步骤3：双击运行

进入解压后的目录，**双击运行**：
```
build_windows.bat
```

脚本会自动：
- ✅ 检查 Python（如未安装会提示）
- ✅ 安装所有依赖
- ✅ 下载 AI 模型（如果缺失）
- ✅ 打包成 .exe
- ✅ 生成安装包（如果安装了 Inno Setup）

---

## 📋 详细步骤

### 前置要求

**1. 安装 Python 3.10+**
- 下载：https://www.python.org/downloads/
- 安装时勾选 "Add Python to PATH"

**2. （可选）安装 Inno Setup**
- 下载：https://jrsoftware.org/isdl.php
- 用于生成专业的安装包

### 手动打包步骤

如果自动脚本失败，可以手动执行：

```cmd
# 1. 进入项目目录
cd SmartFileSearch-v1.0.0-full

# 2. 安装依赖
pip install -r requirements-exe.txt

# 3. 打包成 exe
pyinstaller --clean build.spec

# 4. （可选）生成安装包
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

---

## 📁 打包后的文件

运行 `build_windows.bat` 后，会生成：

```
dist/
├── SmartFileSearch.exe          # 便携版（直接运行）
├── SmartFileSearch-Setup.exe    # 安装包（双击安装）
└── SmartFileSearch/             # 完整目录（包含依赖）
    ├── SmartFileSearch.exe
    ├── data/
    │   └── models/
    │       └── phi-2.Q4_K_M.gguf
    ├── config.yaml
    └── ...
```

---

## 🎯 两种使用方式

### 方式1：便携版（无需安装）

1. 进入 `dist/SmartFileSearch/` 目录
2. 双击 `SmartFileSearch.exe`
3. 直接使用

**优点：** 无需安装，可放在U盘运行

### 方式2：安装包（推荐）

1. 双击 `SmartFileSearch-Setup.exe`
2. 按向导安装
3. 在开始菜单找到快捷方式
4. 运行使用

**优点：** 自动创建快捷方式，专业体验

---

## 🔧 配置文件说明

### build.spec（PyInstaller 配置）

已配置好：
- 包含所有 Python 依赖
- 包含 data/ 目录（模型）
- 包含 config.yaml
- 设置图标和版本信息

### installer.iss（Inno Setup 脚本）

已配置好：
- 安装向导界面
- 创建桌面快捷方式
- 创建开始菜单
- 卸载功能

---

## ⚠️ 常见问题

**Q: 提示"未安装 Python"？**

A: 下载安装 Python 3.10+
   - 访问 https://www.python.org/downloads/
   - 安装时勾选 "Add Python to PATH"

**Q: PyInstaller 打包失败？**

A: 手动安装依赖：
```cmd
pip install PyQt6 whoosh python-docx openpyxl PyYAML loguru watchdog chardet llama-cpp-python pyinstaller
```

**Q: 模型下载太慢？**

A: 可以手动下载：
1. 访问 https://huggingface.co/TheBloke/phi-2-GGUF
2. 下载 `phi-2.Q4_K_M.gguf`
3. 放到 `data/models/` 目录

**Q: 没有 Inno Setup，能生成安装包吗？**

A: 可以！只运行 PyInstaller，会生成便携版 exe
   - 位于 `dist/SmartFileSearch.exe`
   - 可以直接运行，无需安装

**Q: exe 在其他电脑上无法运行？**

A: 需要包含完整的 `dist/SmartFileSearch/` 目录
   - 不要只复制 .exe 文件
   - 整个目录一起复制（包含 DLL 和依赖）

---

## 📊 文件大小预估

| 组件 | 大小 |
|------|------|
| Python 依赖 | ~200MB |
| AI 模型 | ~1.7GB |
| **便携版总计** | **~2GB** |
| **安装包** | **~1.8GB**（压缩后） |

---

## 🎁 快速测试

如果您想先测试，可以：

**1. 直接在 Linux 上运行**
```bash
cd ~/smart-file-search
./start.sh
```

**2. 或使用现有的 tar.gz 包**
```bash
# 解压
tar -xzf SmartFileSearch-v1.0.0-full.tar.gz

# 进入目录
cd SmartFileSearch-v1.0.0-full

# 安装依赖（如果在 Linux 上）
pip install -r requirements.txt

# 运行
./start.sh
```

---

## 💡 建议

如果您经常需要在多台电脑使用，建议：

1. **生成安装包** - 一次打包，到处安装
2. **上传到云盘** - 方便随时下载
3. **创建便携版** - 放在U盘，即插即用

---

## 📞 需要帮助？

如果在 Windows 上打包遇到问题，可以：
1. 查看错误信息
2. 检查 Python 版本
3. 手动安装依赖
4. 或联系我获取远程协助

---

**总结：**
- ✅ tar.gz 包已准备好
- ✅ Windows 打包脚本已准备好
- ✅ 只需在 Windows 上双击 `build_windows.bat`
- ✅ 自动生成 exe 和安装包
