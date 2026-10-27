from datetime import date, datetime

from typing import Literal
from openai import BaseModel
from pydantic import Field


class AftercareCreate(BaseModel):
    """创建后援记录时接受的请求数据"""

    title:str=Field(min_length=1,max_length=200)
    platform:str | None=Field(default=None,max_length=100)
    purchase_date:date | None=None
    return_deadline:date | None=None
    warranty_deadline:date | None=None
    status: Literal["pending", "processing", "completed"] = "pending"
    notes:str | None=None

class AftercareResponse(BaseModel):
    """返回个客户端的后援记录"""
    id: int
    title: str
    platform: str | None
    purchase_date: date | None
    return_deadline: date | None
    warranty_deadline: date | None
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime

    # 允许pydantic直接读取ORM对象并转换成响应
    model_config = {"from_attributes":True}