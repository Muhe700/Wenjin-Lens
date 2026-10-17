# -*- coding: utf-8 -*-
"""
app.models.schemas
==================
系统各模块之间数据交互的规范化契约模型 (Data Transfer Objects / Schemas)。
定义了期刊元数据、评级结果、中科院预警风险、检索响应、台账记录及统计数据的标准接口。
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class JournalBasicDTO(BaseModel):
    """期刊基础身份信息。"""
    name: str = Field(..., description="期刊官方名称")
    publisher: Optional[str] = Field(None, description="主办单位 / 出版社")
    issn: Optional[str] = Field(None, description="国际标准刊号 ISSN")
    cn: Optional[str] = Field(None, description="国内统一刊号 CN")
    level: Optional[str] = Field(None, description="目录初始级别 (A1/A2/A3/A4/B)")
    category: Optional[str] = Field(None, description="目录分级大类名称")
    serial: Optional[int] = Field(None, description="目录序号")


class LevelInfoDTO(BaseModel):
    """广中医重要期刊评级认定结果。"""
    level: Optional[str] = Field(None, description="最终认定级别代码 (A1/A2/A3/A4/B)，若待核验/未符合则为 None")
    label: str = Field(..., description="评级中文描述 (如: A类1级 (顶尖权威) 或 不符合/待核验)")
    reasons: List[str] = Field(default_factory=list, description="定级与升级规则判定依据列表")
    upgraded: bool = Field(default=False, description="是否触发了备注1升级从高认定")


class WarningInfoDTO(BaseModel):
    """中科院国际期刊预警风险排查信息。"""
    is_warned: bool = Field(False, description="是否被列入预警名单")
    name: Optional[str] = Field(None, description="预警期刊官方英文名称")
    issn: Optional[str] = Field(None, description="预警期刊 ISSN")
    year: Optional[str] = Field(None, description="预警年份")
    risk_level: Optional[str] = Field(None, description="风险层级 (高/中/低/预警)")
    reason: Optional[str] = Field(None, description="预警主要原因 (论文工厂/引用操纵/学术合规等)")
    publisher: Optional[str] = Field(None, description="出版商")
    subject: Optional[str] = Field(None, description="学科领域")
    warning_text: Optional[str] = Field(None, description="综合提示文案")


class JournalCandidateDTO(BaseModel):
    """模糊匹配候选期刊条目。"""
    name: str = Field(..., description="候选期刊名称")
    publisher: Optional[str] = Field(None, description="主办或出版机构")
    issn: Optional[str] = Field(None, description="刊号")
    level: Optional[str] = Field(None, description="目录级别")


class SearchResponseDTO(BaseModel):
    """选刊综合检索统一响应契约。"""
    type: str = Field(..., description="响应类型: journal / rule / rule_need_zone / candidates / not_found")
    name: Optional[str] = Field(None, description="匹配到的期刊名称")
    matched_by: Optional[str] = Field(None, description="匹配策略说明 (如: 核心库精确匹配, ISSN匹配等)")
    in_catalog: Optional[bool] = Field(None, description="是否属于广中医校办目录内期刊")
    catalog: Optional[Dict[str, Any]] = Field(None, description="目录层级元数据")
    kb: Optional[Dict[str, Any]] = Field(None, description="知识库已核验全景数据 (9项维度)")
    warning_info: Optional[WarningInfoDTO] = Field(None, description="中科院预警风险信息")
    level_info: Optional[LevelInfoDTO] = Field(None, description="最终评级认定结论与依据")
    track_row: Optional[Dict[str, Any]] = Field(None, description="沉淀至决策台账的标准单行数据")
    # 规则类响应专属字段
    rule_key: Optional[str] = Field(None, description="命中的规则标识")
    level: Optional[str] = Field(None, description="规则映射级别代码")
    label: Optional[str] = Field(None, description="规则映射级别标签")
    note: Optional[str] = Field(None, description="规则补充说明")
    zone: Optional[int] = Field(None, description="命中中科院分区号 (1~4)")
    disclaimer: Optional[str] = Field(None, description="历史版本及服务关停免责说明")
    has_catalog_list: Optional[bool] = Field(False, description="是否支持展开查看该索引下挂期刊全文")
    catalog_list_title: Optional[str] = Field(None, description="展开期刊全文标题")
    # 提示与候选字段
    message: Optional[str] = Field(None, description="状态提示或引导文案")
    candidates: Optional[List[Dict[str, Any]]] = Field(None, description="多条候选期刊列表")


class CasJournalsResponseDTO(BaseModel):
    """中科院1~4区开源镜像期刊列表响应契约。"""
    total: int = Field(..., description="符合条件的期刊总数")
    page: int = Field(1, description="当前页码")
    page_size: int = Field(20, description="每页记录数")
    disclaimer: str = Field(..., description="历史版本及关停免责说明")
    journals: List[Dict[str, Any]] = Field(default_factory=list, description="期刊列表")


class RefreshResponseDTO(BaseModel):
    """联网深度查证与回写响应契约。"""
    status: str = Field(..., description="查证状态: success / error / warning")
    journal: str = Field(..., description="查证目标期刊名称")
    data: Dict[str, Any] = Field(default_factory=dict, description="回写至知识库的 9 维核心指标")
    open_academic: Optional[Dict[str, Any]] = Field(None, description="免Key开放学术生态 (OpenAlex/DOAJ) 事实数据")
    message: Optional[str] = Field(None, description="执行说明")


class TrackResponseDTO(BaseModel):
    """决策台账列表数据响应契约。"""
    total: int = Field(..., description="已归档的期刊总数")
    records: List[Dict[str, Any]] = Field(default_factory=list, description="台账行记录列表 (12列标准表头)")


class CatalogResponseDTO(BaseModel):
    """官方目录全景数据响应契约。"""
    meta: Dict[str, Any] = Field(default_factory=dict, description="目录元数据 (依据文件号、发文单位等)")
    categories: List[Dict[str, Any]] = Field(default_factory=list, description="各级别期刊分类列表 (A1~B)")
    total_journals: int = Field(..., description="目录内期刊总数")
    journals: List[Dict[str, Any]] = Field(default_factory=list, description="目录内全量期刊扁平列表")
    rules: List[Dict[str, Any]] = Field(default_factory=list, description="目录定级与升级折算规则")


class AllIndexesResponseDTO(BaseModel):
    """权威索引与多目录全景聚合数据契约。"""
    gzucms: Dict[str, Any] = Field(..., description="广中医308号目录及规则全量数据")
    chinese_core: Dict[str, Any] = Field(..., description="全国中文核心/CSCD扩充数据库")
    cas_warning: Dict[str, Any] = Field(..., description="中科院国际预警期刊数据库")


class LocateResponseDTO(BaseModel):
    """跨目录期刊精准定位响应契约。"""
    query: str = Field(..., description="查询关键词或期刊名称")
    found: bool = Field(..., description="是否在任一目录中命中")
    summary: str = Field(..., description="定位结果综合提炼文案")
    matches: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict, description="各目录命中条目与定位信息")


class StatsResponseDTO(BaseModel):
    """系统运行全量资产统计契约。"""
    catalog_journals: int = Field(..., description="广中医重要期刊基准总数 (308号文)")
    catalog_rules: int = Field(..., description="通用索引定级规则总数")
    chinese_core_count: int = Field(..., description="全国中文核心/CSCD扩充数据库总数")
    cas_warning_count: int = Field(..., description="中科院国际预警期刊总数")
    kb_records: int = Field(..., description="知识库已沉淀期刊数")
    kb_verified: int = Field(..., description="已完成深度指标核验的期刊数")
    track_records: int = Field(..., description="选刊决策台账已记录条数")
