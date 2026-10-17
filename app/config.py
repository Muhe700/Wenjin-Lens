# -*- coding: utf-8 -*-
"""
app.config
==========
全局配置管理与文件路径解析服务。
统一管理 data/、config/ 与环境变量的加载，支持向后兼容。
"""
import json
import os
import sys

def get_project_root():
    """获取项目根目录绝对路径（兼容 PyInstaller 打包与常规运行）。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    # app/config.py 的父目录的父目录即为项目根目录
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROJECT_ROOT = get_project_root()
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
CATALOG_DATA_DIR = os.path.join(DATA_DIR, "catalog")
KB_DATA_DIR = os.path.join(DATA_DIR, "kb")
TRACK_DATA_DIR = os.path.join(DATA_DIR, "track")
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")

# 确保运行时目录存在
for d in (DATA_DIR, RAW_DATA_DIR, CATALOG_DATA_DIR, KB_DATA_DIR, TRACK_DATA_DIR, CONFIG_DIR):
    os.makedirs(d, exist_ok=True)


def get_catalog_json_path():
    """获取检索目录 JSON 路径（优先 data/catalog/，后向兼容根目录）。"""
    primary = os.path.join(CATALOG_DATA_DIR, "journal_catalog.json")
    if os.path.exists(primary):
        return primary
    fallback = os.path.join(PROJECT_ROOT, "journal_catalog.json")
    if os.path.exists(fallback):
        return fallback
    return primary


def get_catalog_csv_path():
    """获取检索目录 CSV 路径。"""
    primary = os.path.join(CATALOG_DATA_DIR, "journal_catalog.csv")
    if os.path.exists(primary):
        return primary
    fallback = os.path.join(PROJECT_ROOT, "journal_catalog.csv")
    if os.path.exists(fallback):
        return fallback
    return primary


def get_kb_json_path():
    """获取知识库 JSON 路径（优先 data/kb/，后向兼容根目录）。"""
    primary = os.path.join(KB_DATA_DIR, "journal_kb.json")
    if os.path.exists(primary):
        return primary
    fallback = os.path.join(PROJECT_ROOT, "journal_kb.json")
    if os.path.exists(fallback):
        return fallback
    return primary


def get_track_csv_path():
    """获取追踪表 CSV 路径（统一存放在 data/track/）。"""
    return os.path.join(TRACK_DATA_DIR, "journal_track.csv")


def get_track_xlsx_path():
    """获取追踪表 Excel 路径（统一存放在 data/track/）。"""
    return os.path.join(TRACK_DATA_DIR, "journal_track.xlsx")


def get_config_json_path():
    """获取配置文件路径（优先 config/config.json，后向兼容根目录）。"""
    primary = os.path.join(CONFIG_DIR, "config.json")
    if os.path.exists(primary):
        return primary
    fallback = os.path.join(PROJECT_ROOT, "config.json")
    if os.path.exists(fallback):
        return fallback
    return primary


def load_config_data():
    """加载配置 JSON 文件数据字典。"""
    cfg_file = get_config_json_path()
    if os.path.exists(cfg_file):
        try:
            with open(cfg_file, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def get_api_key(explicit_key=None):
    """安全读取 API Key：
    优先级：命令行显式指定 > 系统环境变量 GEMINI_API_KEY > config/config.json > None。
    物理隔离保障：不在代码或公共仓库留存任何明文 Key。"""
    if explicit_key and explicit_key.strip():
        return explicit_key.strip()
    key = os.getenv("GEMINI_API_KEY")
    if key and key.strip():
        return key.strip()
    data = load_config_data()
    val = data.get("gemini_api_key", "").strip()
    if val and val != "YOUR_GEMINI_API_KEY_HERE":
        return val
    return None


def get_proxy():
    """读取本地网络代理设置：
    优先级：config.json 中的 proxy > 系统环境变量 HTTPS_PROXY / HTTP_PROXY > None。"""
    data = load_config_data()
    val = data.get("proxy", "").strip()
    if val:
        return val
    for env_k in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
        env_val = os.getenv(env_k)
        if env_val and env_val.strip():
            return env_val.strip()
    return None


def get_gemini_base_url():
    """获取 Gemini API 基础接入点地址（支持 Cloudflare Worker / 自建反向代理）。
    优先级：环境变量 GEMINI_BASE_URL > config.json 中的 gemini_base_url > 官方默认端点。
    """
    env_url = os.getenv("GEMINI_BASE_URL")
    if env_url and env_url.strip():
        return env_url.strip().rstrip("/")
    data = load_config_data()
    val = data.get("gemini_base_url", "").strip()
    if val:
        return val.rstrip("/")
    return "https://generativelanguage.googleapis.com"

