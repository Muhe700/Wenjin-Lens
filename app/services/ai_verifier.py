# -*- coding: utf-8 -*-
"""
app.services.ai_verifier
========================
基于 Google AI Studio (Gemini) 的期刊数据联网核验服务。
支持本地网络代理适配、候选模型竞选降级与纯标准库零外部依赖。
"""
from datetime import date
import json
import re
import urllib.error
import urllib.request
from app.config import get_api_key, get_proxy, get_gemini_base_url


def fetch_journal_from_gemini(journal_name, api_key=None, proxy=None):
    """通过 Google AI Studio (Gemini) 联网核验期刊指标。
    支持自动探测本地代理、多模型自动竞选回退。
    返回: (success: bool, data_or_err: dict | str)
    """
    api_key = get_api_key(api_key)
    if not api_key:
        return False, "未配置有效的 Gemini API Key（请在 config/config.json 或环境变量设置）"

    proxy_url = proxy or get_proxy()
    if proxy_url:
        proxy_handler = urllib.request.ProxyHandler({"https": proxy_url, "http": proxy_url})
        opener = urllib.request.build_opener(proxy_handler)
    else:
        opener = urllib.request.build_opener()

    prompt = (
        f"你是一名中国高校科研选刊专家。请查证学术期刊《{journal_name}》的真实官方数据。\n"
        "严格返回且仅返回一个合法的纯 JSON 格式对象，不要包含任何前言、后记、注释或 markdown 格式标记。\n"
        "JSON 键名与数据类型规范如下：\n"
        "{\n"
        f'  "basic": {{"name": "{journal_name}", "issn": "string", "cn": "string", "publisher": "string"}},\n'
        '  "indexes": {\n'
        '    "indexes_verified": true,\n'
        '    "scie_zone": null,\n'
        '    "ssci_zone": null,\n'
        '    "cscd_core": false,\n'
        '    "cscd_ext": false,\n'
        '    "cssci_core": false,\n'
        '    "cssci_ext": false,\n'
        '    "pkucore": false,\n'
        '    "chss_core": false,\n'
        '    "ahci": false,\n'
        '    "ei": false,\n'
        '    "cpci_s": false, "cpci_ssh": false, "isr": false, "xhwd": false, "rdfy": false,\n'
        '    "extra": ["string"]\n'
        '  },\n'
        '  "impact_factor": {"jcr_year": 2024, "jcr_if": "string", "cas_zone": "string", "note": "string"},\n'
        '  "editor_in_chief": {"name": "string", "affiliation": "string"},\n'
        '  "scope": "办刊宗旨、学科范畴及主要栏目、字数规约",\n'
        '  "review_cycle": "官方审稿承诺时限及实际作者经验周期",\n'
        '  "publication_mode": "OA或非OA模式、出版周期",\n'
        '  "apc_fee": "版面费或APC收费标准及币种",\n'
        '  "submission_url": "官方采编系统或在线投稿网址（含防伪避坑提示）",\n'
        '  "indexes_note": "收录核验依据",\n'
        '  "sources": ["查证参考的官方或权威网页URL列表"],\n'
        f'  "updated": "{date.today().isoformat()}"\n'
        "}"
    )

    models_to_try = ["gemini-flash-lite-latest", "gemini-flash-latest", "gemini-3.8-flash"]
    last_err = None

    base_url = get_gemini_base_url()
    for model in models_to_try:
        url = f"{base_url}/v1beta/models/{model}:generateContent?key={api_key}"
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "x-goog-api-key": api_key,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 WenjinLens/2.2",
        }
        req_body = {"contents": [{"parts": [{"text": prompt}]}]}
        req_data = json.dumps(req_body, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=req_data, headers=headers)

        try:
            with opener.open(req, timeout=35) as resp:
                resp_body = resp.read().decode("utf-8")
                res_obj = json.loads(resp_body)
                candidates = res_obj.get("candidates", [])
                if not candidates:
                    last_err = "模型未返回任何结果"
                    continue
                parts = candidates[0].get("content", {}).get("parts", [])
                text = "".join(p.get("text", "") for p in parts)
                clean_text = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
                clean_text = re.sub(r"\s*```$", "", clean_text)
                json_match = re.search(r"(\{.*\})", clean_text, re.DOTALL)
                if json_match:
                    clean_text = json_match.group(1)
                data = json.loads(clean_text)
                return True, data
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8", errors="ignore")
            last_err = f"Google API 响应异常 ({model} - HTTP {e.code}): {err_msg}"
            continue
        except urllib.error.URLError as e:
            last_err = f"网络连接失败: {e.reason}（请检查本地代理配置）"
            break
        except Exception as e:
            last_err = f"处理异常: {str(e)}"
            continue

    return False, last_err or "所有候选模型均无法完成请求"
