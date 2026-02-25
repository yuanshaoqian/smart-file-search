@echo off
REM Smart File Search - Windows 安装包生成脚本
REM 需要在 Windows 上运行

echo ================================================
echo    Smart File Search - Windows 安装包生成
echo ================================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未安装 Python，请先安装 Python 3.10+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查 PyInstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [安装] 正在安装 PyInstaller...
    pip install pyinstaller
)

REM 安装依赖
echo [1/4] 安装项目依赖...
pip install -r requirements-exe.txt

REM 下载模型（如果不存在）
if not exist "data\models\phi-2.Q4_K_M.gguf" (
    echo [2/4] 下载 AI 模型...
    echo 这可能需要几分钟，请耐心等待...
    python -c "import urllib.request; urllib.request.urlretrieve('https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf', 'data/models/phi-2.Q4_K_M.gguf')"
)

REM 打包成 exe
echo [3/4] 打包可执行文件...
pyinstaller --clean build.spec

REM 检查 Inno Setup
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    echo [4/4] 生成安装包...
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
    echo.
    echo ================================================
    echo    完成！
    echo ================================================
    echo.
    echo 安装包位置: dist\SmartFileSearch-Setup-v1.0.0.exe
    echo.
) else (
    echo.
    echo ================================================
    echo    打包完成（便携版）
    echo ================================================
    echo.
    echo 可执行文件位置: dist\SmartFileSearch.exe
    echo.
    echo 提示: 如需生成安装包，请安装 Inno Setup
    echo 下载地址: https://jrsoftware.org/isdl.php
    echo.
)

pause
