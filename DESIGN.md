# DESIGN.md — 文津·选刊助手视觉系统设计规范
> 基于 VoltAgent/awesome-design-md 规范标准构建

```yaml
version: alpha
name: Wenjin-Lens-Academic-Design
description: >
  A warm-canvas editorial design system for Wenjin-Lens (文津·选刊助手),
  synthesized from the elite design systems in VoltAgent/awesome-design-md (Claude, Notion, Linear).
  It anchors on a warm cream canvas (#faf9f5), serif display typography (Noto Serif SC) with measured
  negative tracking, scholar pine teal (#1b4942) and warm terracotta (#cc785c) accents, hairline-defined surfaces (#e8e4dc),
  and expansive, breathing whitespace that delivers high academic credibility and serene clarity.

colors:
  primary: "#1b4942"                # 松烟青: 学者底蕴
  primary-hover: "#133732"
  primary-subtle: "#edf5f3"
  on-primary: "#ffffff"

  accent-coral: "#cc785c"           # 朱砂陶: 核心操作与警示温润过渡
  accent-coral-subtle: "#fdf3ef"
  accent-coral-border: "#f3d2c7"

  accent-amber: "#c4841d"           # 晚杏金: 重点晋级与高光
  accent-amber-subtle: "#fdf8ee"

  ink: "#141413"                    # 浓墨: 主标题与刊名
  body: "#3d3d3a"                   # 黛墨: 正文字体
  muted: "#6c6a64"                  # 烟灰: 次要与辅助说明
  muted-light: "#9c9a92"            # 云灰: 元数据标签

  canvas: "#faf9f5"                 # 温润宣纸白: 页面底色
  canvas-soft: "#f4f2eb"            # 次级画布
  surface: "#ffffff"                # 纯白卡片表面
  surface-hover: "#fcfbf9"

  hairline: "#e8e4dc"               # 极细发丝边线
  hairline-soft: "#f0ece4"

  # 等级属性标签色彩 (Notion / Claude 属性胶囊风格)
  badge-a1-bg: "#fdf2ed"
  badge-a1-text: "#b84729"
  badge-a1-border: "#f6cebe"

  badge-a2-bg: "#fdf8ee"
  badge-a2-text: "#9e6b0a"
  badge-a2-border: "#f8e7be"

  badge-a3-bg: "#eef6fc"
  badge-a3-text: "#23689b"
  badge-a3-border: "#cde3f5"

  badge-a4-bg: "#edf7ed"
  badge-a4-text: "#2d7a46"
  badge-a4-border: "#cbe6cb"

  badge-b-bg: "#f5f5f7"
  badge-b-text: "#55555c"
  badge-b-border: "#e1e1e6"

typography:
  display-headline:
    fontFamily: "'Noto Serif SC', 'Songti SC', 'Tiempos Headline', serif"
    fontSize: "30px"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.5px"

  section-title:
    fontFamily: "'Noto Serif SC', 'Songti SC', serif"
    fontSize: "20px"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "-0.2px"

  body-sans:
    fontFamily: "'Plus Jakarta Sans', 'Inter', -apple-system, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.7
    letterSpacing: "0px"

  label-micro:
    fontFamily: "'Plus Jakarta Sans', 'Inter', sans-serif"
    fontSize: "11px"
    fontWeight: 600
    textTransform: "uppercase"
    letterSpacing: "0.6px"

elevation:
  hairline-card: "1px solid #e8e4dc"
  hairline-subtle: "1px solid #f0ece4"
  diffuse-ambient: "0 1px 3px rgba(20, 20, 19, 0.02), 0 4px 16px rgba(20, 20, 19, 0.02)"
  diffuse-float: "0 8px 30px rgba(20, 20, 19, 0.05)"

layout:
  max-width: "1120px"
  section-spacing: "3rem"
  card-padding: "2.25rem 2.5rem"
  grid-gap: "1.5rem"
```
