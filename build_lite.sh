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
cp -r "$PROJECT_ROOT/docs" "$BUILD_DIR/portable/$PACKAGE_NAME/" 2>/dev/null || true
cp -r "$PROJECT_ROOT/hooks" "$BUILD_DIR/portable/$PACKAGE_NAME/"
cp "$PROJECT_ROOT"/*.py "$BUILD_DIR/portable/$PACKAGE_NAME/" 2>/dev/null || true
cp "$PROJECT_ROOT"/*.md "$BUILD_DIR/portable/$PACKAGE_NAME/"
cp "$PROJECT_ROOT"/*.yaml "$BUILD_DIR/portable/$PACKAGE_NAME/"
cp "$PROJECT_ROOT"/*.txt "$BUILD_DIR/portable/$PACKAGE_NAME/"
cp "$PROJECT_ROOT"/*.sh "$BUILD_DIR/portable/$PACKAGE_NAME/"
cp "$PROJECT_ROOT"/*.bat "$BUILD_DIR/portable/$PACKAGE_NAME/" 2>/dev/null || true
cp "$PROJECT_ROOT"/*.spec "$BUILD_DIR/portable/$PACKAGE_NAME/" 2>/dev/null || true
cp "$PROJECT_ROOT"/*.iss "$BUILD_DIR/portable/$PACKAGE_NAME/" 2>/dev/null || true

# 创建数据目录结构（不包含模型）
echo "创建数据目录结构..."
mkdir -p "$BUILD_DIR/portable/$PACKAGE_NAME/data/models"
mkdir -p "$BUILD_DIR/portable/$PACKAGE_NAME/data/indexdir"
mkdir -p "$BUILD_DIR/portable/$PACKAGE_NAME/logs"

# 创建模型下载说明
cat > "$BUILD_DIR/portable/$PACKAGE_NAME/data/models/README.md" << 'EOF'
# AI 模型下载说明

此轻量版包含完整的 AI 支持（llama-cpp-python 已集成），只需下载模型文件即可。

## 下载模型

### Phi-2 模型（推荐，约1.6GB）

```bash
cd data/models
# 使用 wget
wget -O phi-2.Q4_K_M.gguf \
  https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf

# 或使用 curl
curl -L -o phi-2.Q4_K_M.gguf \
  https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf
```

### 其他推荐模型

| 模型 | 大小 | 内存需求 | 说明 |
|------|------|----------|------|
| Phi-2 Q4_K_M | 1.6GB | 4GB+ | 平衡速度和质量 |
| Llama-3.2-1B Q4 | 700MB | 2GB+ | 快速，低内存 |
| Mistral-7B Q4 | 4GB | 8GB+ | 高质量 |

## 配置

下载后，编辑 `config.yaml`:

```yaml
ai:
  enabled: true
  model_path: "data/models/phi-2.Q4_K_M.gguf"
```

## 注意

- AI 功能在打包的 Windows 可执行文件中已集成，无需额外安装 Python 包
- GPU 加速会自动检测（支持 CUDA/Metal）
- 首次加载模型可能需要几分钟

## 故障排除

如果模型加载失败，检查：
1. 模型文件是否完整下载
2. config.yaml 中的路径是否正确
3. 系统内存是否足够
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
