#!/usr/bin/env bash
# ========================================================
# 文津·选刊助手 (Wenjin-Lens) Linux / macOS 一键启动脚本
# ========================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================================"
echo "  文津·选刊助手 (Wenjin-Lens) Web 服务启动中..."
echo "========================================================"

# 检测 Python 版本
if command -v python3 &>/dev/null; then
    PY_CMD="python3"
elif command -v python &>/dev/null; then
    PY_CMD="python"
else
    echo "[错误] 未检测到 Python，请先安装 Python 3.9+"
    exit 1
fi

# 检查虚拟环境（如有）
if [ -d "venv" ]; then
    echo "激活虚拟环境: venv"
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "激活虚拟环境: .venv"
    source .venv/bin/activate
fi

# 检查依赖
echo "正在检查依赖组件..."
$PY_CMD -m pip install -r requirements.txt -q

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
WORKERS="${WORKERS:-2}"

echo ""
echo "  访问地址: http://${HOST}:${PORT}"
echo "  接口文档: http://${HOST}:${PORT}/docs"
echo "========================================================"
echo ""

exec $PY_CMD web_app.py --host "$HOST" --port "$PORT" --workers "$WORKERS"
