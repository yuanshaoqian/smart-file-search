# Smart File Search 打包指南

本文档详细说明如何将 Smart File Search 项目打包成 Windows 可执行文件和安装包。

## 目录

1. [打包内容](#打包内容)
2. [环境准备](#环境准备)
3. [PyInstaller 打包](#pyinstaller-打包)
4. [Inno Setup 安装包](#inno-setup-安装包)
5. [便携版制作](#便携版制作)
6. [AI 模型处理](#ai-模型处理)
7. [常见问题](#常见问题)

## 打包内容

打包后的应用程序包含以下部分：

- **主程序**：基于 PyQt6 的图形界面应用程序
- **依赖库**：所有 Python 依赖包
- **配置文件**：config.yaml（带默认配置）
- **AI 模型**：Phi-2 2.7B Q4_K_M GGUF 模型（约 1.6GB）
- **文档文件**：README.md, PROJECT_DESIGN.md
- **索引目录**：data/indexdir（用户索引数据）
- **日志目录**：logs（应用程序日志）

## 环境准备

### Windows 打包环境

1. **安装 Python 3.8+**
   - 从 [python.org](https://python.org) 下载安装程序
   - 安装时勾选 "Add Python to PATH"

2. **安装依赖工具**
   ```cmd
   pip install -r requirements-exe.txt
   ```

3. **安装 Inno Setup（可选，用于创建安装包）**
   - 从 [jrsoftware.org](https://jrsoftware.org/isdl.php) 下载安装
   - 安装后添加 Inno Setup 的安装目录到 PATH

### Linux 打包环境（用于准备便携版）

本项目的打包脚本可在 Linux 环境下准备便携版压缩包：

```bash
# 给予执行权限
chmod +x build_portable.sh

# 运行打包脚本
./build_portable.sh
```

该脚本会：
- 下载 AI 模型（如果尚未下载）
- 创建包含所有源文件、配置和模型的压缩包
- 生成 Windows 构建脚本

## PyInstaller 打包

### 配置文件说明

`build.spec` 是 PyInstaller 的配置文件，包含以下关键配置：

- **主脚本**：`src/main.py`
- **隐藏导入**：所有可能被 PyInstaller 遗漏的模块
- **数据文件**：配置文件、文档、AI 模型等
- **排除模块**：减少打包体积（如开发工具）
- **运行时钩子**：解决 PyQt6 的插件路径问题

### 执行打包

在 Windows 上执行：

```cmd
# 方法1：使用 spec 文件
pyinstaller build.spec --clean --noconfirm

# 方法2：直接指定主脚本（使用默认配置）
pyinstaller src/main.py --name SmartFileSearch --windowed --onefile --add-data "config.yaml;." --add-data "data;data" --hidden-import PyQt6.QtCore --hidden-import whoosh.fields
```

### 打包输出

成功打包后，会在 `dist/` 目录下生成：

```
dist/SmartFileSearch/
├── SmartFileSearch.exe      # 主程序
├── config.yaml              # 配置文件
├── data/                    # 数据目录
│   ├── models/             # AI 模型
│   └── indexdir/           # 索引目录
├── docs/                    # 文档
├── PyQt6/                  # Qt6 运行时库
└── ... 其他依赖库
```

## Inno Setup 安装包

### 脚本说明

`installer.iss` 是 Inno Setup 的安装脚本，包含以下功能：

- 创建开始菜单和桌面快捷方式
- 注册文件关联
- 安装运行时依赖检查
- 创建必要的数据目录
- 添加卸载程序

### 编译安装包

1. 打开 Inno Setup Compiler
2. 加载 `installer.iss` 文件
3. 点击 "Compile" 按钮
4. 安装包将输出到 `Output/` 目录

### 自定义选项

可以根据需要修改脚本中的以下变量：

```pascal
#define MyAppName "Smart File Search"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Your Company"
#define MyAppURL "https://yourwebsite.com"
```

## 便携版制作

### 什么是便携版

便携版是一个压缩包，解压后即可运行，无需安装。包含：

- 预编译的可执行文件（如果已构建）
- 所有依赖库
- AI 模型文件
- 配置文件

### 创建便携版

如果已经在 Windows 上完成 PyInstaller 打包，可以创建便携版：

1. 将 `dist/SmartFileSearch` 目录复制到新文件夹
2. 确保包含所有必要文件
3. 使用 7-Zip 或 WinRAR 创建压缩包：
   ```cmd
   "C:\Program Files\7-Zip\7z.exe" a -tzip SmartFileSearch-Portable.zip SmartFileSearch\
   ```

### Linux 脚本自动打包

`build_portable.sh` 脚本可以自动创建便携版压缩包（不含可执行文件，但包含所有构建所需文件）：

```bash
./build_portable.sh
```

输出文件：`build/SmartFileSearch-portable-v1.0.0.tar.gz`

## AI 模型处理

### 模型下载

项目使用 Phi-2 2.7B Q4_K_M GGUF 模型，约 1.6GB。打包时模型文件已包含在 `data/models/` 目录。

如果模型文件不存在，打包脚本会自动下载：

```bash
# 手动下载模型
mkdir -p data/models
cd data/models
wget https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf
```

### 模型配置

确保 `config.yaml` 中的 AI 配置指向正确的模型路径：

```yaml
ai:
  enabled: false  # 设为 true 启用 AI 功能
  model_path: "data/models/phi-2.Q4_K_M.gguf"
```

### 内存要求

- 模型加载需要约 2GB RAM
- 推理需要额外 1-2GB RAM
- 推荐系统内存 8GB+

## 常见问题

### 1. PyInstaller 打包失败

**问题**：`ModuleNotFoundError` 或 `ImportError`

**解决**：
- 检查 `hidden_imports` 是否包含缺失的模块
- 手动添加隐藏导入：`--hidden-import module_name`
- 确保所有依赖已安装：`pip install -r requirements-exe.txt`

### 2. PyQt6 相关错误

**问题**：应用程序启动时崩溃，报错关于 Qt 插件

**解决**：
- 确保 `hooks/pyi_rth_pyqt6.py` 包含在打包中
- 检查 Qt 插件路径是否正确
- 尝试添加环境变量：`set QT_DEBUG_PLUGINS=1`

### 3. AI 模型无法加载

**问题**：AI 功能启用后模型加载失败

**解决**：
- 确认模型文件存在且路径正确
- 检查文件完整性（下载可能中断）
- 确保有足够的内存（8GB+）
- 查看日志文件 `logs/app.log` 获取详细错误

### 4. 文件索引问题

**问题**：索引目录权限错误或无法创建

**解决**：
- 确保应用程序有写入权限
- 检查 `data/indexdir` 目录是否存在
- 在配置中修改索引目录路径

### 5. 安装包太大

**问题**：生成的安装包超过 2GB

**解决**：
- 压缩 AI 模型（已使用 GGUF 格式）
- 使用 UPX 压缩可执行文件（已在 spec 中启用）
- 排除不必要的开发文件

## 高级配置

### 交叉编译

虽然 PyInstaller 不支持交叉编译，但可以通过以下方式在 Linux 上准备 Windows 打包：

1. 使用 Wine 运行 Python for Windows
2. 在 Wine 环境中安装 PyInstaller
3. 通过 Wine 执行打包命令

示例脚本见 `build_wine.sh`（可选创建）。

### 代码签名

为 Windows 可执行文件添加数字签名：

```cmd
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com SmartFileSearch.exe
```

### 版本信息

在 `build.spec` 中添加版本信息：

```python
exe = EXE(
    ...
    version='version_info.txt',
    ...
)
```

创建 `version_info.txt` 文件定义版本、公司、版权等信息。

## 维护说明

### 更新依赖

当更新 Python 依赖时：

1. 更新 `requirements.txt` 和 `requirements-exe.txt`
2. 重新安装依赖：`pip install -r requirements-exe.txt --upgrade`
3. 重新打包测试

### 更新模型

要更换 AI 模型：

1. 下载新的 GGUF 模型到 `data/models/`
2. 更新 `config.yaml` 中的 `model_path`
3. 重新打包应用程序

### 发布流程

1. 更新版本号（config.yaml 和 installer.iss）
2. 运行完整的测试套件
3. 在 Windows 上执行 PyInstaller 打包
4. 创建安装包和便携版
5. 验证安装包功能
6. 发布到下载服务器

## 联系支持

如有打包问题，请查看项目 GitHub Issues 或联系开发团队。

---
*文档最后更新：2024-02-23*