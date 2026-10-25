from typing import Literal

from pydantic import BaseModel, Field, field_validator


# Literal--类型限制（输入约束）
class Message(BaseModel):
    """单条聊天消息"""
    role:Literal["system","user","assistant"]
    content:str=Field(
        min_length=1,
        max_length=4000,
        description="消息内容"
    )
#     拦截纯空格信息
    @field_validator("content")
    @classmethod
    def validate_content(cls,value:str)->str:
        if not value.strip():
            raise  ValueError("消息内容不能为空格")
        return value

class ChatRequest(BaseModel):
    """聊天请求模型"""

    session_id:str|None=Field(
        default=None,
        min_length=1,
        max_length=100,
        description="会话ID，不传则不启动跨请求记忆"
    )
    messages:list[Message]=Field(
        min_length=1,
        description="聊天消息列表"
    )


class ChatResponse(BaseModel):
    """聊天响应模型"""
    answer:str=Field(
        description="AI 返回的回答"
    )