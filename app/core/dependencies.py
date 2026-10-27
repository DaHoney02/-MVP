"""FastAPI 依赖注入：为请求提供业务服务。"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.chat_service import ChatService
from app.db.database import get_db


def get_chat_service(
    db: Session = Depends(get_db),
) -> ChatService:
    """创建绑定当前请求数据库 Session 的聊天服务。"""
    return ChatService(db=db)