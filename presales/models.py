from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

Status = Literal["supported", "unsupported", "pending"]
Role = Literal["sales", "reviewer"]
Deployment = Literal["cloud", "private"]
STATUS_LABELS = {"supported": "已支持", "unsupported": "明确不支持", "pending": "待确认"}
CAPABILITY_LABELS = {"wecom_sso": "企业微信登录", "excel_export": "Excel导出", "private_deploy": "私有部署",
    "ai_summary": "AI会议总结", "data_residency": "数据驻留", "ldap": "LDAP登录", "offline_client": "离线客户端",
    "performance": "性能与SLA", "audit_log": "审计日志", "disaster_recovery": "跨区域容灾",
    "open_api": "开放API", "pricing": "报价", "certification": "认证证明", "unknown": "未识别范围"}
FLAG_LABELS = {"roadmap": "路线图不构成交付承诺", "conflict": "当前资料存在冲突",
               "historical": "包含历史资料", "missing": "缺少可用依据",
               "parameter": "需求参数尚未得到证据支持", "unapproved": "包含未审核资料"}


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Source(Contract):
    id: str
    title: str
    capability: str
    aliases: list[str]
    version: str
    deployment: list[Deployment]
    lifecycle: Literal["current", "archived", "roadmap"] = "current"
    approved: bool = True
    access: Role = "sales"
    stance: Status
    content: str = Field(min_length=1)
    owner: str
    updated_at: str
    synthetic: bool = True


class Requirement(Contract):
    id: str
    text: str = Field(min_length=1, max_length=2000)
    capability: str = "unknown"
    parameter_uncertain: bool = False


class Citation(Contract):
    doc_id: str
    title: str
    version: str
    quote: str
    lifecycle: str
    authoritative: bool


class Assessment(Contract):
    requirement: Requirement
    status: Status
    answer: str
    reason: str
    citations: list[Citation] = Field(default_factory=list)
    flags: list[str] = Field(default_factory=list)
    reviewer_action: Literal["approve", "return"] | None = None
    reviewer_note: str = ""
    reviewed_answer: str | None = None


class ExtractedItem(Contract):
    text: str = Field(min_length=1, max_length=2000)
    capability: str
    parameter_uncertain: bool = False


class Extraction(Contract):
    items: list[ExtractedItem] = Field(min_length=1, max_length=40)


class Review(Contract):
    item_id: str
    action: Literal["approve", "return"]
    answer: str = Field(min_length=1, max_length=4000)
    note: str = Field(default="", max_length=2000)

    @field_validator("answer")
    @classmethod
    def strip_answer(cls, value):
        if not value.strip():
            raise ValueError("答复不能为空")
        return value.strip()
