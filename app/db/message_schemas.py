from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


# 用于校验客户端提交的数据
class MessageCreate(BaseModel):
    session_id:str=Field(min_length=1,max_length=100)
    role:str=Field(pattern=r"^(user|assistant|system)$")
    content:str=Field(min_length=1,max_length=10000)

# 用于规定返回的数据结构    from_attributes---让pydantic可以从SQLAlchemy模型对象中读读取属性
class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:int
    session_id:str
    role:str
    content:str
    created_at:datetime