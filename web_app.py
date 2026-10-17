# -*- coding: utf-8 -*-
"""
web_app.py — 文津·选刊助手 Web 服务启动入口
===========================================
启动本地 FastAPI + Web 前端服务，提供学术检索界面与开放 RESTful API。

用法：
  python web_app.py             # 默认在 http://127.0.0.1:8000 启动
  python web_app.py --port 8080 # 指定端口
  python web_app.py --host 0.0.0.0 # 允许局域网其他设备访问
"""
import argparse
import os
import sys
import uvicorn

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


def main():
    parser = argparse.ArgumentParser(description="文津·选刊助手 (Wenjin-Lens) Web 服务")
    default_host = os.getenv("HOST", "0.0.0.0")
    default_port = int(os.getenv("PORT", "8000"))
    default_workers = int(os.getenv("WORKERS", "1"))

    parser.add_argument("--host", default=default_host, help=f"服务监听地址 (默认: {default_host})")
    parser.add_argument("--port", type=int, default=default_port, help=f"服务监听端口 (默认: {default_port})")
    parser.add_argument("--workers", type=int, default=default_workers, help="工作进程数 (生产部署推荐: 2~4, 默认: 1)")
    parser.add_argument("--reload", action="store_true", help="代码热重载开发模式 (仅限单进程调试)")
    args = parser.parse_args()

    print("\n" + "=" * 65)
    print("  文津·选刊助手 (Wenjin-Lens) Web 服务正在启动...")
    print(f"  > 本机电脑访问地址: http://127.0.0.1:{args.port}")
    if args.host == "0.0.0.0":
        try:
            import socket
            ips = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")]
            lan_ips = [ip for ip in ips if ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172.")] or ips
            for lan_ip in lan_ips:
                print(f"  > 同局域网访问地址 (手机/其他电脑): http://{lan_ip}:{args.port}")
        except Exception:
            pass
    print(f"  > 交互式 API 文档:  http://127.0.0.1:{args.port}/docs")
    if not args.reload and args.workers > 1:
        print(f"  > 生产多进程集群:  {args.workers} workers")
    print("=" * 65 + "\n")

    uvicorn_kwargs = {
        "host": args.host,
        "port": args.port,
        "reload": args.reload,
        "app_dir": BASE_DIR,
    }
    if not args.reload and args.workers > 1:
        uvicorn_kwargs["workers"] = args.workers

    uvicorn.run("app.web.api:app", **uvicorn_kwargs)


if __name__ == "__main__":
    main()
