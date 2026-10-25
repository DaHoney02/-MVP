"""数据库的CRUR（增删查改）"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import MessageRecord
from app.schemas.schemas import Message

def create_message(
    db: Session,
    session_id: str,
    role: str,
    content: str,
) -> MessageRecord:
    message = MessageRecord(
        session_id=session_id,
        role=role,
        content=content,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def create_messages(
        db:Session,
        session_id:str,
        messages:list[Message],
)->None:
    """批量新增一轮对话。所有消息假如同一事务，再统一提交"""

    if not messages:
        return

    records=[
        MessageRecord(
            session_id=session_id,
            role=message.role,
            content=message.content
        )for message in messages
    ]

    try:
        db.add_all(records)  #只将对象加入当前Session，暂不逐条提交
        db.commit()  #提交消息
    except Exception:
        db.rollback()  #发生数据库错误时回滚当前事务
        raise

def get_message(
        db:Session,
        message_id:int,
)->MessageRecord | None:
    """按消息ID查询一条消息"""
    return db.get(MessageRecord,message_id)


def list_messages(
        db:Session,
        session_id:str,
)->list[MessageRecord]:
    """按会话查询消息，按创建时间和ID排序"""
    statement=(
        select(MessageRecord)
        .where(MessageRecord.session_id==session_id)
        .order_by(MessageRecord.created_at,MessageRecord.id)
    )
    # db.scalars(statement).all()---获取查询结果
    return list(db.scalars(statement).all())

def update_message(
        db:Session,
        message_id:int,
        new_content:str
)->MessageRecord | None:
    """修改消息内容"""
    # db.get(model,id)---按主键查询
    message=db.get(MessageRecord,message_id)
    if message is None:
        return None

    message.content=new_content
    db.commit()
    db.refresh(message)
    return message

def delete_message(
        db:Session,
        message_id:int,
)->bool:
    """删除消息：返回是否找到并删除消息"""
    message=db.get(MessageRecord,message_id)
    if message is None:
        return False

    db.delete(message)
    db.commit()
    return True


def list_chat_messages(
        db:Session,
        session_id:str,
)->list[Message]:
    """读取数据库历史记录，转换为聊天模型需要的消息格式"""
    statement=(
        select(MessageRecord)
        .where(MessageRecord.session_id == session_id)
        .order_by(MessageRecord.created_at,MessageRecord.id)

    )
    records=db.scalars(statement).all()
    print("records:",records)
    return [
        Message(role=record.role,content=record.content)
        for record in records
    ]


