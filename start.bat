@echo off
REM Smart File Search 启动脚本 (Windows)
REM 用法: start.bat [--init] [--debug] [--help]

chcp 65001 >nul
setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM 颜色定义（Windows 10+ 支持）
if "%1"=="--help" goto help

echo ================================
echo    Smart File Search
echo ================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python
    echo 请安装 Python 3.10 或更高版本
    pause
    exit /b 1
)

REM 检查 Python 版本
for /f "tokens=2" %%i in ('python -c "import sys; print(sys.version_info.major, sys.version_info.minor)" 2^>nul') do set PYTHON_MINOR=%%i
for /f "tokens=1" %%i in ('python -c "import sys; print(sys.version_info.major, sys.version_info.minor)" 2^>nul') do set PYTHON_MAJOR=%%i

if %PYTHON_MAJOR% lss 3 (
    echo [错误] Python 版本过低
    echo 需要 Python 3.10 或更高版本
    pause
    exit /b 1
)

if %PYTHON_MAJOR% equ 3 if %PYTHON_MINOR% lss 10 (
    echo [错误] Python 版本过低 (3.%PYTHON_MINOR%)
    echo 需要 Python 3.10 或更高版本
    pause
    exit /b 1
)

echo [OK] Python 版本: %PYTHON_MAJOR%.%PYTHON_MINOR%

REM 检查依赖
echo.
echo [信息] 检查 Python 依赖...
if not exist "requirements.txt" (
    echo [错误] 未找到 requirements.txt
    pause
    exit /b 1
)

python -c "import PyQt6" 2>nul
if errorlevel 1 (
    echo [警告] 缺少依赖，正在安装...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)

REM 创建必要目录
if not exist "data\indexdir" mkdir "data\indexdir"
if not exist "data\models" mkdir "data\models"
if not exist "logs" mkdir "logs"
if not exist "docs" mkdir "docs"

echo [OK] 目录结构已创建

REM 解析参数
set INIT_INDEX=0
set DEBUG_MODE=0

:parse_args
if "%1"=="" goto end_args
if "%1"=="--init" set INIT_INDEX=1
if "%1"=="--debug" set DEBUG_MODE=1
if "%1"=="--help" goto help
shift
goto parse_args

:end_args

REM 初始化索引
if %INIT_INDEX% equ 1 (
    echo.
    echo [信息] 初始化文件索引...
    python src\main.py --init
    if errorlevel 1 (
        echo [错误] 索引初始化失败
        pause
        exit /b 1
    )
    echo [OK] 索引初始化完成
)

REM 启动应用
echo.
echo [信息] 启动 Smart File Search...

if %DEBUG_MODE% equ 1 (
    python src\main.py --debug
) else (
    python src\main.py
)

set EXIT_CODE=%errorlevel%

if %EXIT_CODE% neq 0 (
    echo [错误] 应用异常退出，代码: %EXIT_CODE%
    echo 查看 logs\app.log 获取详细信息
)

pause
exit /b %EXIT_CODE%

:help
echo.
echo Smart File Search 启动脚本
echo.
echo 用法: start.bat [选项]
echo.
echo 选项:
echo   --init      初始化索引（首次运行或重建索引）
echo   --debug     启用调试模式，输出详细日志
echo   --help      显示此帮助信息
echo.
echo 示例:
echo   start.bat          正常启动应用
echo   start.bat --init   创建初始文件索引
echo.
pause
exit /b 0