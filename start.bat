  @echo off
chcp 65001 >nul
TITLE 社交平台自动上传工具 - 一键启动

echo ========================================
echo   社交平台自动上传工具 - 一键启动
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.8+
    echo.
    echo 下载地址: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [信息] 正在启动启动器...
echo.

REM 启动Python启动器
python launcher.py

if errorlevel 1 (
    echo.
    echo [错误] 启动失败，请检查错误信息
    pause
)

