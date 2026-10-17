# ========================================================
# 文津·选刊助手 (Wenjin-Lens) 生产级 Docker 镜像构建文件
# ========================================================
FROM python:3.10-slim

# 设置运行期环境变量，关闭 pyc 生成与 stdout 缓冲
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    HOST=0.0.0.0 \
    PORT=8000 \
    WORKERS=2

WORKDIR /app

# 优先复制依赖清单，最大化利用 Docker 构建层缓存
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制系统全部代码与离线数据资产
COPY . /app/

# 确保运行时可写目录存在
RUN mkdir -p /app/data/track /app/config

# 暴露 Web 端口
EXPOSE 8000

# 容器健康检查（使用 Python 原生标准库，无需额外安装外部依赖）
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')" || exit 1

# 启动 Web 服务
CMD ["python", "web_app.py", "--host", "0.0.0.0", "--port", "8000"]
