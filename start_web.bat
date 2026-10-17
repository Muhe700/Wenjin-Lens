@echo off
chcp 65001 >nul
title 文津·选刊助手 (Wenjin-Lens)

echo ========================================================
echo   文津·选刊助手 (Wenjin-Lens) 一键启动器
echo ========================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python 环境，请确保已安装 Python 3.9+ 并加入系统 PATH。
    pause
    exit /b 1
)

echo [1/2] 正在检查依赖环境...
pip install -r requirements.txt -q

echo.
echo [2/2] 正在启动文津·选刊助手 Web 服务...
echo   本地访问: http://127.0.0.1:8000
echo   API 文档: http://127.0.0.1:8000/docs
echo.
python web_app.py --host 127.0.0.1 --port 8000

pause
