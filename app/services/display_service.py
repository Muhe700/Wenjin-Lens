# -*- coding: utf-8 -*-
"""
app.services.display_service
============================
终端交互与 9 项核心选刊维度高读性渲染服务。
"""
from app.core.constants import LEVEL_LABEL, OWN_JOURNALS
from app.core.rules import compute_level


def format_journal_display(journal_rec, kb_rec, catalog, matched_by="精确匹配", kb_only=False):
    """组装 9 项选刊核心指标输出文本。"""
    name = journal_rec["name"]
    lines = []
    if matched_by and matched_by != "精确匹配":
        lines.append(f"提示：按“{matched_by}”命中以下期刊。")
    if kb_only:
        lines.append("期刊（目录外已核验期刊）：" + name)
    else:
        lines.append(f"期刊：{name}")
    if journal_rec.get("publisher"):
        lines.append(f"主办/出版：{journal_rec['publisher']}")
    issn_cn = []
    if journal_rec.get("issn"):
        issn_cn.append(f"ISSN {journal_rec['issn']}")
    if journal_rec.get("cn"):
        issn_cn.append(f"CN {journal_rec['cn']}")
    if issn_cn:
        lines.append(f"刊号：{' | '.join(issn_cn)}")

    # 风险排查：中科院预警期刊
    from app.services.risk_service import check_cas_warning
    issn_val = journal_rec.get("issn") or (kb_rec or {}).get("basic", {}).get("issn")
    warn = check_cas_warning(name, issn_val)
    if warn:
        lines.append("")
        lines.append("!" * 75)
        lines.append(f"【⚠️ 风险警示】：该刊已被列入《中国科学院文献情报中心国际期刊预警名单》！")
        lines.append(f"  - 预警年份：{warn['year']}年")
        lines.append(f"  - 预警原因：{warn['reason']}")
        lines.append(f"  - 避坑提示：多数高校职称评审与科研绩效已明确不予认定或经费不报销，请务必审慎投稿！")
        lines.append("!" * 75)

    lines.append("")

    # [1] 收录索引
    lines.append("[1] 收录索引")
    if kb_rec and (kb_rec.get("indexes") or {}).get("indexes_verified"):
        idx = kb_rec["indexes"]
        known = []
        if idx.get("scie_zone"):
            known.append(f"SCIE（中科院{idx['scie_zone']}区）")
        if idx.get("ssci_zone"):
            known.append(f"SSCI（中科院{idx['ssci_zone']}区）")
        for field, label in (
            ("cscd_core", "CSCD核心版"),
            ("cscd_ext", "CSCD扩展版"),
            ("cssci_core", "CSSCI核心版"),
            ("cssci_ext", "CSSCI扩展版"),
            ("pkucore", "北大核心（中文核心期刊要目总览）"),
            ("chss_core", "中国人文社会科学核心期刊要览"),
            ("ahci", "A&HCI"),
            ("ei", "EI Compendex"),
            ("cpci_s", "CPCI-S"),
            ("cpci_ssh", "CPCI-SSH"),
            ("isr", "ISR"),
            ("xhwd", "新华文摘全文转载"),
            ("rdfy", "人大复印报刊资料全文转载"),
        ):
            if idx.get(field):
                known.append(label)
        if known:
            lines.append("  " + "；".join(known))
        else:
            lines.append("  知识库核验：未命中广中医目录涉及的主流索引（详见下方核验说明）")
        if kb_rec.get("indexes_note"):
            lines.append(f"  索引核验说明：{kb_rec['indexes_note']}")
    else:
        lines.append("  知识库暂无核验数据，需联网检索确认（运行 --refresh 联网查证）")
    lines.append("")

    # [2] 广中医认定
    lines.append("[2] 广中医重要期刊认定")
    best, reasons, upgraded = compute_level(catalog, None if kb_only else journal_rec, kb_rec)
    if best:
        lines.append(f"  认定级别：{LEVEL_LABEL[best]}")
        for r_ in reasons:
            lines.append(f"    - {r_}")
        if upgraded:
            lines.append("    - 按目录备注1：本表所列刊物如进入更高级别，则按高级别期刊认定")
        if kb_only:
            lines.append("    - 该刊不在目录 B 类列名内，级别由 A 类索引规则计算得出；收录情况随年份变化，以职称评审当年为准")
    else:
        lines.append("  未命中目录及索引规则，需人工核实")
    lines.append("")

    # [3]-[9] 知识库动态字段
    kb = kb_rec or {}
    if_ = kb.get("impact_factor") or {}
    if if_:
        parts = []
        if if_.get("jcr_if"):
            parts.append(f"JCR影响因子 {if_.get('jcr_if')}（{if_.get('jcr_year', '')}）")
        if if_.get("cas_zone"):
            parts.append(f"中科院分区 {if_.get('cas_zone')}")
        lines.append(f"[3] 评分：{'；'.join(parts)}")
        if if_.get("note"):
            lines.append(f"    说明：{if_['note']}")
    else:
        lines.append("[3] 评分：知识库暂无（影响因子/中科院分区待检索核验）")
    editor = kb.get("editor_in_chief") or {}
    if editor.get("name"):
        lines.append(
            f"[4] 主编：{editor['name']}"
            + (f"（{editor.get('affiliation', '')}）" if editor.get("affiliation") else "")
        )
    else:
        lines.append("[4] 主编：知识库暂无，待检索核验")
    if kb.get("scope"):
        lines.append(f"[5] 收稿方向：{kb['scope']}")
    else:
        lines.append("[5] 收稿方向：知识库暂无，待检索核验")
    if kb.get("review_cycle"):
        lines.append(f"[6] 审稿周期：{kb['review_cycle']}")
    else:
        lines.append("[6] 审稿周期：知识库暂无，待检索核验")
    if kb.get("publication_mode"):
        lines.append(f"[7] 出版方式：{kb['publication_mode']}")
    else:
        lines.append("[7] 出版方式：知识库暂无，待检索核验")
    if kb.get("apc_fee"):
        lines.append(f"[8] 版面费（APC）：{kb['apc_fee']}")
    else:
        lines.append("[8] 版面费（APC）：知识库暂无，待检索核验")
    if kb.get("submission_url"):
        lines.append(f"[9] 投稿方式与防伪：{kb['submission_url']}")
    else:
        lines.append("[9] 投稿方式与防伪：知识库暂无，待检索核验")

    # 目录备注
    if name in OWN_JOURNALS:
        lines.append("")
        lines.append(
            "【目录备注4】本单位期刊《"
            + name
            + "》：每人每次职称申报时仅可使用 1 篇作为有效业绩。"
        )
    lines.append("")
    lines.append("数据来源：data/catalog/ (广中医308号文) + data/kb/ (知识库核验)")
    lines.append("已自动记录到追踪表 data/track/journal_track.xlsx（--track 查看）")
    return "\n".join(lines)


def format_rule_display(rule_key, level, rule_name):
    """格式化单条索引规则查询结果。"""
    out = [f"索引规则：{rule_name}", f"对应广中医级别：{LEVEL_LABEL[level]}"]
    if rule_key.startswith("scie") or rule_key.startswith("ssci"):
        out.append("说明：SCIE/SSCI 分区按论文正式发表当年版本认定（详见目录备注2、3）")
    return "\n".join(out)
