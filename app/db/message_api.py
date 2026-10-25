
from fastapi import APIRouter, Depends,HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.message_repository import create_message, list_messages
from app.db.message_schemas import MessageRead, MessageCreate

message_router=APIRouter(tags=["messages"])

@message_router.post(
    "/messages",
    response_model=MessageRead
)
# 保存
def save_message(
        request:MessageCreate,
        db:Session=Depends(get_db)
):
    return create_message(
        db=db,
        session_id=request.session_id,
        role=request.role,
        content=request.content
    )

@message_router.get(
    "/sessions/{session_id}/messages",
    response_model=list[MessageRead]
)
# 查询
def read_messages(
        session_id:str,
        db:Session=Depends(get_db)
):
    messages=list_messages(db,session_id)

    if not messages:
        raise HTTPException(
            status_code=404,
            detail="该会话暂无消息"
        )
    return messages