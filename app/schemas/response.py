from typing import TypeVar, Generic
from uuid import uuid4

from pydantic import BaseModel, Field

# 统一成功响应结构

T=TypeVar("T")  #TypeVar --定义泛型变量:绑定什么类型就变成类型

# Generic 泛型（=模版）
class ResponseModel(BaseModel,Generic[T]):
    code:int=0
    message:str="success"
    data:T|None=None
    trace_id:str=Field(
        default_factory=lambda:uuid4().hex,  #每次创建响应对象时，若调用方没有传入，则自动生成新的ID
        description="请求追踪ID"
    )