#!/bin/bash

# Smart File Search 启动脚本 (Linux/macOS)
# 用法: ./start.sh [--init] [--debug] [--help]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 帮助信息
show_help() {
    echo "Smart File Search 启动脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --init      初始化索引（首次运行或重建索引）"
    echo "  --debug     启用调试模式，输出详细日志"
    echo "  --help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0          正常启动应用"
    echo "  $0 --init   创建初始文件索引"
    echo ""
}

# 检查 Python 版本
check_python() {
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}错误: 未找到 python3${NC}"
        echo "请安装 Python 3.10 或更高版本"
        exit 1
    fi
    
    python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    python_major=$(python3 -c 'import sys; print(sys.version_info.major)')
    python_minor=$(python3 -c 'import sys; print(sys.version_info.minor)')
    
    if [ $python_major -lt 3 ] || { [ $python_major -eq 3 ] && [ $python_minor -lt 10 ]; }; then
        echo -e "${RED}错误: Python 版本过低 (${python_version})${NC}"
        echo "需要 Python 3.10 或更高版本"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Python 版本: ${python_version}${NC}"
}

# 检查依赖
check_dependencies() {
    echo -e "${YELLOW}检查 Python 依赖...${NC}"
    
    if [ ! -f "requirements.txt" ]; then
        echo -e "${RED}错误: 未找到 requirements.txt${NC}"
        exit 1
    fi
    
    # 检查是否已安装 pip
    if ! command -v pip3 &> /dev/null; then
        echo -e "${YELLOW}警告: 未找到 pip3，尝试安装...${NC}"
        if command -v apt-get &> /dev/null; then
            sudo apt-get install -y python3-pip
        elif command -v yum &> /dev/null; then
            sudo yum install -y python3-pip
        elif command -v brew &> /dev/null; then
            brew install python3
        else
            echo -e "${RED}错误: 无法自动安装 pip3${NC}"
            echo "请手动安装 pip3 后重试"
            exit 1
        fi
    fi
    
    # 检查主要依赖
    if ! python3 -c "import PyQt6" 2>/dev/null; then
        echo -e "${YELLOW}安装缺失的依赖...${NC}"
        pip3 install -r requirements.txt --user
    fi
    
    echo -e "${GREEN}✓ 依赖检查完成${NC}"
}

# 初始化索引
init_index() {
    echo -e "${YELLOW}初始化文件索引...${NC}"
    python3 src/main.py --init
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 索引初始化完成${NC}"
    else
        echo -e "${RED}索引初始化失败${NC}"
        exit 1
    fi
}

# 创建必要目录
create_directories() {
    mkdir -p data/indexdir
    mkdir -p data/models
    mkdir -p logs
    mkdir -p docs
    
    echo -e "${GREEN}✓ 目录结构已创建${NC}"
}

# 主函数
main() {
    INIT_INDEX=false
    DEBUG_MODE=false
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --init)
                INIT_INDEX=true
                shift
                ;;
            --debug)
                DEBUG_MODE=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                echo -e "${RED}未知参数: $1${NC}"
                show_help
                exit 1
                ;;
        esac
    done
    
    echo -e "${GREEN}=== Smart File Search ===${NC}"
    
    # 执行检查
    check_python
    check_dependencies
    create_directories
    
    # 初始化索引（如果需要）
    if [ "$INIT_INDEX" = true ]; then
        init_index
    fi
    
    # 启动应用
    echo -e "${YELLOW}启动 Smart File Search...${NC}"
    
    if [ "$DEBUG_MODE" = true ]; then
        python3 src/main.py --debug
    else
        python3 src/main.py
    fi
    
    exit_code=$?
    
    if [ $exit_code -ne 0 ]; then
        echo -e "${RED}应用异常退出，代码: ${exit_code}${NC}"
        echo "查看 logs/app.log 获取详细信息"
    fi
    
    exit $exit_code
}

# 运行主函数
main "$@"