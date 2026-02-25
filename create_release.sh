#!/bin/bash
# 创建便携版和安装包

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION="1.0.0"
DIST_DIR="$PROJECT_ROOT/dist"

echo "=== Smart File Search 打包脚本 ==="
echo

# 清理旧的构建文件
echo "清理旧的构建文件..."
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR/SmartFileSearch"

# 复制可执行文件
echo "复制可执行文件..."
cp -r "$PROJECT_ROOT/dist/SmartFileSearch.exe" "$DIST_DIR/SmartFileSearch/" 2>/dev/null || echo "警告: SmartFileSearch.exe 不存在，请先运行 PyInstaller"

# 复制必要文件
echo "复制必要文件..."
cp -r "$PROJECT_ROOT/data" "$DIST_DIR/SmartFileSearch/"
cp "$PROJECT_ROOT/config.yaml" "$DIST_DIR/SmartFileSearch/"
cp "$PROJECT_ROOT/README.md" "$DIST_DIR/SmartFileSearch/"
cp "$PROJECT_ROOT/start.bat" "$DIST_DIR/SmartFileSearch/"
cp "$PROJECT_ROOT/LICENSE" "$DIST_DIR/SmartFileSearch/" 2>/dev/null || echo "警告: LICENSE 文件不存在"

# 创建使用说明
cat > "$DIST_DIR/SmartFileSearch/使用说明.txt" << 'EOF'
================================================
   Smart File Search v1.0.0 - 便携版
================================================

🚀 快速开始

1. 双击运行 start.bat
2. 首次运行会自动配置
3. 开始搜索文件

================================================
📁 目录结构

SmartFileSearch/
├── SmartFileSearch.exe  主程序
├── start.bat            启动脚本
├── config.yaml          配置文件
├── data/
│   ├── models/          AI模型
│   └── indexdir/        索引目录
└── logs/                日志文件

================================================
⚙️ 配置

编辑 config.yaml 可以：
- 修改索引目录
- 调整AI参数
- 自定义界面

================================================
💡 功能

✅ 快速文件搜索
✅ AI理解自然语言
✅ 支持Word/Excel/TXT
✅ 完全本地运行

================================================
📚 更多信息

README.md - 详细说明
docs/ - 文档目录

================================================
EOF

# 创建便携版压缩包
echo "创建便携版压缩包..."
cd "$DIST_DIR"
zip -r "SmartFileSearch-portable-v${VERSION}.zip" SmartFileSearch/

# 计算文件大小
SIZE=$(du -sh "SmartFileSearch-portable-v${VERSION}.zip" | cut -f1)

echo
echo "✅ 打包完成！"
echo "📦 文件: SmartFileSearch-portable-v${VERSION}.zip"
echo "📏 大小: $SIZE"
echo "📍 路径: $DIST_DIR/SmartFileSearch-portable-v${VERSION}.zip"
echo
echo "下一步:"
echo "1. 上传到 GitHub Releases"
echo "2. 或使用 GitHub Actions 自动构建"
