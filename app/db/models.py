from datetime import datetime, timezone, date

from sqlalchemy import Integer, String, Text, DateTime, Date, func
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

class AftercareRecord(Base):
    """后援业务记录：管理商品、退货期限和保修信息"""
    __tablename__ = "aftercare_records"

    id:Mapped[int]=mapped_column(
        primary_key=True,
        index=True
    )

    title: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )
    platform:Mapped[str | None]=mapped_column(
        String(100),
        nullable=True
    )

    purchase_date:Mapped[date | None]=mapped_column(
        Date,
        nullable=True
    )

    return_deadline:Mapped[date | None]=mapped_column(
        Date,
        nullable=True
    )

    warranty_deadline:Mapped[date | None]=mapped_column(
        Date,
        nullable=True
    )

    status:Mapped[str]=mapped_column(
        String(30),
        nullable=False,
        default="pending"
    )

    notes:Mapped[str | None]=mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    updated_at:Mapped[datetime]=mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
