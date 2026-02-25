#!/bin/bash
# 轻量级打包脚本（不含AI模型）
# 模型需要单独下载

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$PROJECT_ROOT/build"
VERSION="1.0.0"
PACKAGE_NAME="SmartFileSearch-portable-v${VERSION}-lite"

echo "=== Smart File Search 轻量级打包 ==="
echo "项目根目录: $PROJECT_ROOT"
echo "构建目录: $BUILD_DIR"
echo "输出文件: ${PACKAGE_NAME}.tar.gz"
echo

# 清理
echo "清理旧的构建文件..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/portable/$PACKAGE_NAME"

# 复制源代码
echo "复制源代码..."
cp -r "$PROJECT_ROOT/src" "$BUILD_DIR/portable/$PACKAGE_NAME/"
cp -r "$PROJECT_ROOT/docs" "$BUILD_DIR/portable/$PACKAGE_NAME/"
cp "$PROJECT_ROOT"/*.py "$BUILD_DIR/portable/$PACKAGE_NAME/" 2>/dev/null || true
cp "$PROJECT_ROOT"/*.md "$BUILD_DIR/portable/$PACKAGE_NAME/"
cp "$PROJECT_ROOT"/*.yaml "$BUILD_DIR/portable/$PACKAGE_NAME/"
cp "$PROJECT_ROOT"/*.txt "$BUILD_DIR/portable/$PACKAGE_NAME/"
cp "$PROJECT_ROOT"/*.sh "$BUILD_DIR/portable/$PACKAGE_NAME/"
cp "$PROJECT_ROOT"/*.bat "$BUILD_DIR/portable/$PACKAGE_NAME/"

# 创建数据目录结构（不包含模型）
echo "创建数据目录结构..."
mkdir -p "$BUILD_DIR/portable/$PACKAGE_NAME/data/models"
mkdir -p "$BUILD_DIR/portable/$PACKAGE_NAME/data/indexdir"
mkdir -p "$BUILD_DIR/portable/$PACKAGE_NAME/logs"

# 创建模型下载说明
cat > "$BUILD_DIR/portable/$PACKAGE_NAME/data/models/README.md" << 'EOF'
# AI 模型下载说明

由于模型文件较大（约1.7GB），未包含在轻量版中。

## 下载 Phi-2 模型（推荐）

```bash
cd ~/smart-file-search/data/models
wget -O phi-2.Q4_K_M.gguf \
  https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf
```

## 或使用配置脚本

运行项目根目录下的 `configure-ai.sh` 自动下载和配置。

## 配置模型

下载后，编辑 `config.yaml`:

```yaml
ai:
  enabled: true
  model_path: "data/models/phi-2.Q4_K_M.gguf"
```

## 其他模型选择

详见 `docs/LOW_SPEC_GUIDE.md`
EOF

# 打包
echo "创建压缩包..."
cd "$BUILD_DIR/portable"
tar -czf "$BUILD_DIR/${PACKAGE_NAME}.tar.gz" "$PACKAGE_NAME"

# 移动到项目根目录
mv "$BUILD_DIR/${PACKAGE_NAME}.tar.gz" "$PROJECT_ROOT/"

# 计算大小
SIZE=$(du -h "$PROJECT_ROOT/${PACKAGE_NAME}.tar.gz" | cut -f1)

echo
echo "✅ 打包完成!"
echo "📦 文件: ${PACKAGE_NAME}.tar.gz"
echo "📏 大小: $SIZE"
echo "📍 路径: $PROJECT_ROOT/${PACKAGE_NAME}.tar.gz"
echo
echo "⚠️  注意: 此版本不包含AI模型"
echo "   请运行 configure-ai.sh 下载模型"
