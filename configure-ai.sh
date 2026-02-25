#!/bin/bash
# AI 模型快速配置脚本
# 自动检测系统内存，推荐并下载适合的模型

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODELS_DIR="$PROJECT_DIR/data/models"
CONFIG_FILE="$PROJECT_DIR/config.yaml"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}   Smart File Search - AI 模型配置向导${NC}"
echo -e "${BLUE}================================================${NC}"
echo

# 检测系统内存（MB）
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    TOTAL_MEM=$(sysctl -n hw.memsize | awk '{print int($1/1024/1024)}')
else
    # Linux
    TOTAL_MEM=$(free -m | awk '/^Mem:/{print $2}')
fi

echo -e "${GREEN}✓${NC} 检测到系统内存: ${YELLOW}${TOTAL_MEM}MB${NC}"
echo

# 根据内存推荐模型
recommend_model() {
    local mem=$1
    
    if [ $mem -lt 4096 ]; then
        # < 4GB
        echo -e "${YELLOW}⚠️  检测到低内存配置（< 4GB）${NC}"
        echo -e "${GREEN}推荐模型:${NC}"
        echo "  1. TinyLlama 1.1B (0.6GB) - 极速模式"
        echo "  2. Qwen 0.5B (0.4GB) - 中文优化"
        echo "  3. 禁用AI功能 - 仅使用索引搜索"
        echo
        echo -ne "${BLUE}请选择 [1-3]: ${NC}"
        read choice
        
        case $choice in
            1) echo "tinyllama-1.1b" ;;
            2) echo "qwen-0.5b" ;;
            3) echo "disable" ;;
            *) echo "tinyllama-1.1b" ;;
        esac
        
    elif [ $mem -lt 8192 ]; then
        # 4-8GB
        echo -e "${YELLOW}⚠️  检测到中等内存配置（4-8GB）${NC}"
        echo -e "${GREEN}推荐模型:${NC}"
        echo "  1. Phi-2 2.7B (1.6GB) - 推荐 ⭐"
        echo "  2. Qwen 1.8B (1.2GB) - 中文优化"
        echo "  3. TinyLlama 1.1B (0.6GB) - 极速模式"
        echo "  4. 禁用AI功能"
        echo
        echo -ne "${BLUE}请选择 [1-4]: ${NC}"
        read choice
        
        case $choice in
            1) echo "phi-2" ;;
            2) echo "qwen-1.8b" ;;
            3) echo "tinyllama-1.1b" ;;
            4) echo "disable" ;;
            *) echo "phi-2" ;;
        esac
        
    else
        # > 8GB
        echo -e "${GREEN}✓ 检测到充足内存配置（> 8GB）${NC}"
        echo -e "${GREEN}推荐模型:${NC}"
        echo "  1. Mistral 7B (4.1GB) - 高质量 ⭐"
        echo "  2. Qwen 7B (4.3GB) - 中文优化 ⭐"
        echo "  3. Phi-2 2.7B (1.6GB) - 快速"
        echo "  4. Llama 2 7B (4.0GB) - 经典"
        echo "  5. 禁用AI功能"
        echo
        echo -ne "${BLUE}请选择 [1-5]: ${NC}"
        read choice
        
        case $choice in
            1) echo "mistral-7b" ;;
            2) echo "qwen-7b" ;;
            3) echo "phi-2" ;;
            4) echo "llama2-7b" ;;
            5) echo "disable" ;;
            *) echo "mistral-7b" ;;
        esac
    fi
}

# 获取用户选择
MODEL_CHOICE=$(recommend_model $TOTAL_MEM)
echo

# 处理选择
if [ "$MODEL_CHOICE" == "disable" ]; then
    echo -e "${YELLOW}禁用AI功能...${NC}"
    
    # 修改配置文件
    if [ -f "$CONFIG_FILE" ]; then
        # 备份配置
        cp "$CONFIG_FILE" "$CONFIG_FILE.backup"
        
        # 使用 Python 修改 YAML（更可靠）
        python3 << EOF
import yaml
with open('$CONFIG_FILE', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)
config['ai']['enabled'] = False
with open('$CONFIG_FILE', 'w', encoding='utf-8') as f:
    yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
EOF
        
        echo -e "${GREEN}✓ 已禁用AI功能${NC}"
        echo -e "${GREEN}✓ 配置已保存到 config.yaml${NC}"
    fi
    
    echo
    echo -e "${GREEN}配置完成！您可以运行 ./start.sh 启动程序${NC}"
    exit 0
fi

# 创建模型目录
mkdir -p "$MODELS_DIR"

# 模型下载信息
declare -A MODELS
MODELS["tinyllama-1.1b"]="https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf|tinyllama-1.1b.Q4_K_M.gguf|0.6"
MODELS["qwen-0.5b"]="https://huggingface.co/Qwen/Qwen1.5-0.5B-Chat-GGUF/resolve/main/qwen1.5-0.5b-chat.Q4_K_M.gguf|qwen-0.5b.Q4_K_M.gguf|0.4"
MODELS["phi-2"]="https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf|phi-2.Q4_K_M.gguf|1.6"
MODELS["qwen-1.8b"]="https://huggingface.co/Qwen/Qwen1.5-1.8B-Chat-GGUF/resolve/main/qwen1.5-1.8b-chat.Q4_K_M.gguf|qwen-1.8b.Q4_K_M.gguf|1.2"
MODELS["mistral-7b"]="https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf|mistral-7b.Q4_K_M.gguf|4.1"
MODELS["qwen-7b"]="https://huggingface.co/Qwen/Qwen1.5-7B-Chat-GGUF/resolve/main/qwen1.5-7b-chat.Q4_K_M.gguf|qwen-7b.Q4_K_M.gguf|4.3"
MODELS["llama2-7b"]="https://huggingface.co/TheBloke/Llama-2-7B-GGUF/resolve/main/llama-2-7b.Q4_K_M.gguf|llama-2-7b.Q4_K_M.gguf|4.0"

# 获取模型信息
IFS='|' read -r URL FILENAME SIZE <<< "${MODELS[$MODEL_CHOICE]}"

echo -e "${GREEN}准备下载模型:${NC}"
echo -e "  模型: ${YELLOW}$MODEL_CHOICE${NC}"
echo -e "  大小: ${YELLOW}${SIZE}GB${NC}"
echo -e "  文件: ${FILENAME}"
echo

# 检查是否已下载
if [ -f "$MODELS_DIR/$FILENAME" ]; then
    echo -e "${GREEN}✓ 模型已存在，跳过下载${NC}"
else
    echo -ne "${BLUE}开始下载? [Y/n]: ${NC}"
    read confirm
    
    if [[ "$confirm" =~ ^[Nn]$ ]]; then
        echo -e "${YELLOW}取消下载${NC}"
        exit 0
    fi
    
    echo -e "${BLUE}开始下载模型...${NC}"
    echo -e "${YELLOW}这可能需要几分钟，请耐心等待...${NC}"
    echo
    
    # 下载模型
    cd "$MODELS_DIR"
    if wget -c --show-progress -O "$FILENAME" "$URL"; then
        echo
        echo -e "${GREEN}✓ 模型下载完成!${NC}"
    else
        echo
        echo -e "${RED}✗ 模型下载失败${NC}"
        echo -e "${YELLOW}请检查网络连接或手动下载:${NC}"
        echo -e "  URL: $URL"
        echo -e "  保存到: $MODELS_DIR/$FILENAME"
        exit 1
    fi
fi

# 配置优化
echo
echo -e "${BLUE}优化配置...${NC}"

# 根据内存设置参数
if [ $TOTAL_MEM -lt 4096 ]; then
    CONTEXT_SIZE=512
    MAX_TOKENS=128
elif [ $TOTAL_MEM -lt 8192 ]; then
    CONTEXT_SIZE=1024
    MAX_TOKENS=256
else
    CONTEXT_SIZE=2048
    MAX_TOKENS=512
fi

# 更新配置文件
if [ -f "$CONFIG_FILE" ]; then
    # 备份配置
    cp "$CONFIG_FILE" "$CONFIG_FILE.backup"
    
    # 使用 Python 修改 YAML
    python3 << EOF
import yaml
with open('$CONFIG_FILE', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

config['ai']['enabled'] = True
config['ai']['model_path'] = 'data/models/$FILENAME'
config['ai']['context_size'] = $CONTEXT_SIZE
config['ai']['max_tokens'] = $MAX_TOKENS

with open('$CONFIG_FILE', 'w', encoding='utf-8') as f:
    yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
EOF
    
    echo -e "${GREEN}✓ 配置已更新:${NC}"
    echo -e "  AI启用: ${GREEN}true${NC}"
    echo -e "  模型路径: ${GREEN}data/models/$FILENAME${NC}"
    echo -e "  上下文长度: ${GREEN}${CONTEXT_SIZE}${NC}"
    echo -e "  最大生成长度: ${GREEN}${MAX_TOKENS}${NC}"
fi

# 检查 llama-cpp-python
echo
echo -e "${BLUE}检查AI依赖...${NC}"
if ! python3 -c "import llama_cpp" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  未安装 llama-cpp-python${NC}"
    echo -ne "${BLUE}是否现在安装? [Y/n]: ${NC}"
    read install
    
    if [[ ! "$install" =~ ^[Nn]$ ]]; then
        echo -e "${BLUE}正在安装 llama-cpp-python...${NC}"
        pip install llama-cpp-python || {
            echo -e "${RED}✗ 安装失败${NC}"
            echo -e "${YELLOW}请手动安装: pip install llama-cpp-python${NC}"
        }
    fi
else
    echo -e "${GREEN}✓ llama-cpp-python 已安装${NC}"
fi

# 完成
echo
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}   配置完成！${NC}"
echo -e "${GREEN}================================================${NC}"
echo
echo -e "${BLUE}下一步:${NC}"
echo -e "  1. 查看配置: ${YELLOW}cat config.yaml${NC}"
echo -e "  2. 启动程序: ${YELLOW}./start.sh${NC}"
echo -e "  3. 测试AI搜索: 在搜索框输入自然语言问题"
echo
echo -e "${BLUE}提示:${NC}"
echo -e "  - 查看详细指南: ${YELLOW}docs/LOW_SPEC_GUIDE.md${NC}"
echo -e "  - 如需更换模型，重新运行此脚本即可"
echo -e "  - 配置备份: ${YELLOW}config.yaml.backup${NC}"
echo
