#!/usr/bin/env bash
# 技术面试系统快捷启动（macOS / Linux / Git Bash）
set -e
cd "$(dirname "$0")"

echo "=============================================="
echo "           技术面试系统 快捷启动"
echo "=============================================="

# ---- 环境检查 ----
command -v node >/dev/null || { echo "[错误] 未检测到 Node.js，请先安装 Node 18+"; exit 1; }
command -v python >/dev/null || command -v python3 >/dev/null || { echo "[错误] 未检测到 Python，请先安装 Python 3.10+"; exit 1; }
PYTHON=$(command -v python || command -v python3)

# ---- 首次运行：安装前端依赖（Electron 走国内镜像） ----
if [ ! -f node_modules/electron/dist/electron.exe ] && [ ! -f node_modules/electron/dist/Electron.app/Contents/MacOS/Electron ]; then
    echo "[首次运行] 安装前端依赖，需要几分钟..."
    ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/ npm install --no-fund --no-audit
fi

# ---- 首次运行：创建 Python 虚拟环境 ----
if [ ! -f .venv/bin/python ] && [ ! -f .venv/Scripts/python.exe ]; then
    echo "[首次运行] 创建 Python 虚拟环境并安装后端依赖..."
    "$PYTHON" -m venv .venv
    VPY=".venv/bin/python"; [ -f .venv/Scripts/python.exe ] && VPY=".venv/Scripts/python.exe"
    "$VPY" -m pip install -q -r backend/requirements.txt || \
        "$VPY" -m pip install -q -r backend/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
fi

echo
echo "启动中：Electron 窗口稍后自动打开（关闭窗口即退出系统）"
echo
npm run dev
