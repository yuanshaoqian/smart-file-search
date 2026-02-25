# GitHub Actions 自动编译指南

## 🎯 目标

通过 GitHub Actions 自动编译 Windows 可执行文件，用户可以直接下载使用，无需搭建编译环境。

---

## 📋 前置要求

1. **GitHub 账号**
2. **项目已上传到 GitHub**
3. **基本配置完成**

---

## 🚀 使用方法

### 方法1：手动触发构建（推荐）

1. **上传项目到 GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/你的用户名/smart-file-search.git
   git push -u origin main
   ```

2. **手动触发构建**
   - 进入 GitHub 仓库页面
   - 点击 "Actions" 标签
   - 选择 "Build Windows Release" 工作流
   - 点击 "Run workflow" 按钮
   - 等待构建完成（约 15-20 分钟）

3. **下载构建产物**
   - 构建完成后，在 "Artifacts" 区域下载
   - 或在 "Releases" 页面下载安装包

---

### 方法2：自动构建（通过标签）

1. **创建版本标签**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **自动触发构建**
   - GitHub Actions 会自动开始构建
   - 自动创建 Release 并上传文件

3. **下载安装包**
   - 在 Releases 页面下载

---

## 📦 构建产物

每次构建会生成两个文件：

1. **SmartFileSearch-Setup.exe** (安装版)
   - 双击安装
   - 自动创建快捷方式
   - 带卸载程序

2. **SmartFileSearch-portable.zip** (便携版)
   - 解压即用
   - 无需安装
   - 可放在U盘

---

## ⚙️ 工作流程

```mermaid
graph LR
    A[触发构建] --> B[设置Python环境]
    B --> C[安装依赖]
    C --> D[下载AI模型]
    D --> E[编译exe]
    E --> F[打包]
    F --> G[上传产物]
    G --> H[创建Release]
```

---

## 🔧 自定义配置

### 修改版本号

编辑 `.github/workflows/build.yml`：

```yaml
env:
  VERSION: "1.0.1"  # 修改这里
```

### 添加其他平台

```yaml
jobs:
  build-windows:
    runs-on: windows-latest
    # ... Windows 配置
  
  build-macos:
    runs-on: macos-latest
    # ... macOS 配置
  
  build-linux:
    runs-on: ubuntu-latest
    # ... Linux 配置
```

### 添加编译优化

```yaml
- name: Build with optimizations
  run: |
    pyinstaller --clean --onefile --windowed \
      --add-data "data:data" \
      --add-data "config.yaml:." \
      --name "SmartFileSearch" \
      src/main.py
```

---

## 📊 构建时间

| 阶段 | 时间 |
|------|------|
| 设置环境 | 2-3 分钟 |
| 安装依赖 | 3-5 分钟 |
| 下载模型 | 5-8 分钟 |
| 编译 exe | 5-8 分钟 |
| 打包上传 | 2-3 分钟 |
| **总计** | **17-27 分钟** |

---

## ⚠️ 常见问题

### Q: 构建失败怎么办？

A: 检查以下几点：
1. `requirements.txt` 是否正确
2. Python 版本是否兼容
3. 依赖包是否可用
4. 查看构建日志定位问题

### Q: 模型下载失败？

A: 修改模型下载方式：
1. 使用镜像站点
2. 或将模型预先上传到仓库
3. 或使用 GitHub Releases 托管模型

### Q: 编译后的 exe 太大？

A: 优化方法：
1. 使用 `--onefile` 减小体积
2. 排除不必要的依赖
3. 使用 UPX 压缩

---

## 🎉 用户使用流程

### 安装版用户：

```
1. 下载 SmartFileSearch-Setup.exe
2. 双击安装
3. 点击桌面快捷方式
4. 开始使用！
```

### 便携版用户：

```
1. 下载 SmartFileSearch-portable.zip
2. 解压到任意目录
3. 双击 start.bat
4. 开始使用！
```

---

## 📝 更新流程

1. **修改代码**
   ```bash
   git add .
   git commit -m "更新功能"
   git push
   ```

2. **发布新版本**
   ```bash
   git tag v1.0.1
   git push origin v1.0.1
   ```

3. **等待自动构建**
   - GitHub Actions 自动编译
   - 自动创建 Release
   - 用户可以下载更新

---

## 🔄 持续集成

建议配置：
- ✅ 每次推送自动测试
- ✅ 标签推送自动构建
- ✅ 手动触发构建
- ✅ 定期构建（每周）

---

## 💡 最佳实践

1. **版本管理**
   - 使用语义化版本号（v1.0.0）
   - 每次更新都要打标签

2. **发布说明**
   - 在 Release 中写清楚更新内容
   - 包含安装说明

3. **用户反馈**
   - 设置 Issue 模板
   - 提供反馈渠道

4. **安全检查**
   - 不要在代码中硬编码密钥
   - 使用 GitHub Secrets

---

## 📞 支持

如果遇到问题：
1. 查看 GitHub Actions 日志
2. 检查项目配置
3. 提交 Issue

---

**现在，用户可以直接下载使用，无需编译！** 🎉
