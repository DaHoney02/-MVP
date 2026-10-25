from fastapi import Depends
from sqlalchemy.orm import Session

from app.chat_service import ChatService
from app.db.database import get_db


# 服务启动请求了一次就不在启动了
def get_chat_service(
        db:Session=Depends(get_db),
)->ChatService:

    return ChatService(db=db)