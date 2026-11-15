@echo off
chcp 65001 >nul
title 技术面试系统
cd /d "%~dp0"

echo ==============================================
echo            技术面试系统 快捷启动
echo ==============================================
echo.

rem ---- 环境检查 ----
where node >nul 2>nul
if errorlevel 1 (
    echo [错误] 未检测到 Node.js，请先安装 Node 18+：https://nodejs.org/
    pause
    exit /b 1
)
where python >nul 2>nul
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+：https://www.python.org/downloads/
    pause
    exit /b 1
)

rem ---- 首次运行：安装前端依赖（Electron 走国内镜像） ----
if not exist "node_modules\electron\dist\electron.exe" (
    if not exist "node_modules" (
        echo [首次运行] 安装前端依赖，需要几分钟...
    ) else (
        echo [首次运行] 补齐 Electron 运行时（国内镜像）...
    )
    set "ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/"
    call npm install --no-fund --no-audit
    if errorlevel 1 (
        echo [错误] 前端依赖安装失败，请检查网络后重试
        pause
        exit /b 1
    )
)

rem ---- 首次运行：创建 Python 虚拟环境 ----
if not exist ".venv\Scripts\python.exe" (
    echo [首次运行] 创建 Python 虚拟环境并安装后端依赖...
    python -m venv .venv
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败，请确认安装 Python 时勾选了 Add to PATH
        pause
        exit /b 1
    )
    ".venv\Scripts\python.exe" -m pip install -q -r "backend\requirements.txt"
    if errorlevel 1 (
        echo 默认源安装失败，改用清华镜像重试...
        ".venv\Scripts\python.exe" -m pip install -q -r "backend\requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple
        if errorlevel 1 (
            echo [错误] 后端依赖安装失败，请检查网络后重试
            pause
            exit /b 1
        )
    )
)

echo.
echo 启动中：Electron 窗口稍后自动打开（关闭窗口即退出系统）
echo.
call npm run dev

echo.
echo 应用已退出。
pause
