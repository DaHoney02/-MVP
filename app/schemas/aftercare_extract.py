from datetime import date

from openai import BaseModel
from pydantic import Field


class AftercareExtractRequest(BaseModel):
    """AI信息提取接口的请求数据"""

    text:str=Field(
        min_length=1,
        max_length=2000,
        description="用户描述后援事项的自然语言"
    )

class AftercareExtractResult(BaseModel):
    """AI提取候选信息"""
    title:str | None=Field(
        default=None,
        description="商品或事项名称"
    )
    platform:str| None=Field(
        default=None,
        description="购买凭条或商家"
    )
    return_deadline: date | None = Field(
        default=None,
        description="退货截止日期；无法确定时为空",
    )

    warranty_deadline: date | None = Field(
        default=None,
        description="保修截止日期；无法确定时为空",
    )

    notes: str | None = Field(
        default=None,
        description="其他有用的事项信息",
    )

    missing_fields: list[str] = Field(
        default_factory=list,
        description="仍然缺失、需要用户补充的字段",
    )

    needs_confirmation: bool = Field(
        default=True,
        description="是否需要用户确认提取结果",
    )