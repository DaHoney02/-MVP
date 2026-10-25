from datetime import datetime, timezone

from sqlalchemy import Integer, String, Text, DateTime
from sqlalchemy.orm import Mapped,mapped_column

from app.db.database import Base

# ORM模型（与数据库中的字段相互映射）
class MessageRecord(Base):
    """持久化保存的聊天消息"""
    __tablename__ = "messages"

    id:Mapped[int]=mapped_column(
        Integer,
        primary_key=True,
        index=True
    )
    session_id:Mapped[str]=mapped_column(
        String(100),
        index=True
    )
    role:Mapped[str]=mapped_column(String(20))
    content:Mapped[str]=mapped_column(Text)
    created_at:Mapped[datetime]=mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
