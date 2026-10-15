
"""生命周期：程序启动初始化资源+关闭释放资源"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.chat_serivce import ChatService


@asynccontextmanager
async def lifespan(app:FastAPI):
    # =====启动=======
    print("服务启动")
    #创建共享对象  app.state---应用级
    app.state.service=ChatService()

    yield

    #======关闭阶段=======
    print("服务关闭")