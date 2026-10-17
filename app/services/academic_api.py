# -*- coding: utf-8 -*-
"""
app.services.academic_api
=========================
开放学术生态接口服务：免注册、免 API Key 直接调用权威开放学术元数据。
整合两大数据源：
  1. OpenAlex API: 获取官方刊名、出版商、主页、OA 模式与官方 APC (USD)
  2. DOAJ API: 获取官方承诺审稿周期（周数）、APC 收费细则及减免政策
"""
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from app.config import get_proxy

POLITE_USER_AGENT = "WenjinLens/2.1 (mailto:academic-lens@wenjin.edu.cn; Pair-Programming Academic Tool)"


def _get_opener():
    proxy_url = get_proxy()
    if proxy_url:
        proxy_handler = urllib.request.ProxyHandler({"https": proxy_url, "http": proxy_url})
        return urllib.request.build_opener(proxy_handler)
    return urllib.request.build_opener()


def fetch_openalex_journal(issn=None, journal_name=None):
    """免注册直接查询 OpenAlex 获取期刊权威元数据。
    返回: dict(success=True, data={...}) 或 dict(success=False, error=...)
    """
    opener = _get_opener()
    clean_issn = re.sub(r"[^0-9Xx-]", "", str(issn or "")).strip()

    def _query_openalex(query_url):
        req = urllib.request.Request(query_url, headers={"User-Agent": POLITE_USER_AGENT})
        with opener.open(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("results", [])

    try:
        results = []
        if clean_issn:
            if len(clean_issn) == 8 and "-" not in clean_issn:
                clean_issn = f"{clean_issn[:4]}-{clean_issn[4:]}"
            results = _query_openalex(f"https://api.openalex.org/sources?filter=issn:{clean_issn}")

        if not results and journal_name:
            encoded_name = urllib.parse.quote(journal_name.strip())
            results = _query_openalex(f"https://api.openalex.org/sources?search={encoded_name}")

        if not results:
            return {"success": False, "error": "OpenAlex 未检索到对应期刊条目"}

        j = results[0]
        summary = {
            "source": "OpenAlex",
            "display_name": j.get("display_name"),
            "publisher": j.get("host_organization_name") or (j.get("publisher") or ""),
            "homepage_url": j.get("homepage_url"),
            "is_oa": j.get("is_oa"),
            "is_in_doaj": j.get("is_in_doaj"),
            "apc_usd": j.get("apc_usd"),
            "apc_prices": j.get("apc_prices") or [],
            "cited_by_count": j.get("cited_by_count"),
            "works_count": j.get("works_count"),
            "h_index": j.get("summary_stats", {}).get("h_index"),
            "issn": j.get("issn"),
            "type": j.get("type"),
        }
        return {"success": True, "data": summary}
    except urllib.error.URLError as e:
        return {"success": False, "error": f"OpenAlex 网络连接异常: {e.reason}"}
    except Exception as e:
        return {"success": False, "error": f"OpenAlex 数据解析异常: {str(e)}"}


def fetch_doaj_journal(issn):
    """免注册直接查询 DOAJ 开放获取期刊数据库。
    返回: 审稿周期（周数）、APC 金额及减免政策
    """
    if not issn:
        return {"success": False, "error": "DOAJ 查询需提供 ISSN"}
    clean_issn = re.sub(r"[^0-9Xx-]", "", str(issn)).strip()
    if len(clean_issn) == 8 and "-" not in clean_issn:
        clean_issn = f"{clean_issn[:4]}-{clean_issn[4:]}"

    opener = _get_opener()
    url = f"https://doaj.org/api/v2/search/journals/issn:{clean_issn}"
    req = urllib.request.Request(url, headers={"User-Agent": POLITE_USER_AGENT})

    try:
        with opener.open(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("results", [])
            if not results:
                return {"success": False, "error": "DOAJ 未收录该刊（非纯OA期刊）"}
            bib = results[0].get("bibjson", {})
            pub_weeks = bib.get("publication_time_weeks")
            apc = bib.get("apc") or {}
            waiver = bib.get("waiver_policy") or {}

            summary = {
                "source": "DOAJ",
                "title": bib.get("title"),
                "publication_time_weeks": pub_weeks,
                "review_cycle_desc": f"官方承诺处理时限中位数约 {pub_weeks} 周" if pub_weeks else None,
                "has_apc": apc.get("has_apc"),
                "apc_max": apc.get("max"),
                "waiver_policy": waiver.get("has_waiver") or waiver.get("url"),
                "oa_start_year": bib.get("oa_start", {}).get("year"),
            }
            return {"success": True, "data": summary}
    except urllib.error.URLError as e:
        return {"success": False, "error": f"DOAJ 网络连接异常: {e.reason}"}
    except Exception as e:
        return {"success": False, "error": f"DOAJ 数据解析异常: {str(e)}"}


def fetch_open_academic_metadata(issn=None, journal_name=None):
    """聚合查询 OpenAlex 与 DOAJ，生成免注册、权威客观的期刊元数据。"""
    res = {
        "openalex": None,
        "doaj": None,
        "apc_summary": "",
        "homepage": "",
        "review_cycle": "",
        "is_oa": None,
    }

    # 1. 查 OpenAlex
    oa_res = fetch_openalex_journal(issn, journal_name)
    if oa_res["success"]:
        res["openalex"] = oa_res["data"]
        d = oa_res["data"]
        if d.get("homepage_url"):
            res["homepage"] = d["homepage_url"]
        if d.get("apc_usd") is not None:
            res["apc_summary"] = f"官方APC: ${d['apc_usd']}"
        res["is_oa"] = d.get("is_oa")

    # 2. 查 DOAJ
    target_issn = issn
    if not target_issn and res.get("openalex"):
        oa_issn = res["openalex"].get("issn")
        if isinstance(oa_issn, list) and oa_issn and oa_issn[0]:
            target_issn = str(oa_issn[0]).strip()
        elif isinstance(oa_issn, str) and oa_issn.strip():
            target_issn = oa_issn.strip()

    if target_issn:
        doaj_res = fetch_doaj_journal(target_issn)
        if doaj_res.get("success"):
            res["doaj"] = doaj_res["data"]
            dd = doaj_res["data"]
            if dd.get("review_cycle_desc"):
                res["review_cycle"] = dd["review_cycle_desc"]
            if not res["apc_summary"] and isinstance(dd.get("apc_max"), list) and dd["apc_max"]:
                max_price = dd["apc_max"][0]
                if isinstance(max_price, dict):
                    res["apc_summary"] = f"APC: {max_price.get('currency', '')} {max_price.get('price', '')}".strip()

    return res
