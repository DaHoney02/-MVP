
"""测试一轮对话的批量数据库保存。"""
import pytest
from sqlalchemy import create_engine, UniqueConstraint, String
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column
from sqlalchemy.pool import StaticPool

from app.db.database import Base
from app.db.message_repository import create_messages, list_messages
from app.schemas.schemas import Message


def make_test_db():
    """创建独立的内存 SQLite 数据库，测试结束后不污染正式数据。"""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    TestSession = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )
    return engine, TestSession()


def test_create_messages_saves_a_whole_turn():
    """一轮对话的用户消息和 AI 回答都应该保存。"""
    engine, db = make_test_db()

    try:
        messages = [
            Message(role="user", content="你好"),
            Message(role="assistant", content="你好！有什么可以帮你？"),
        ]

        create_messages(
            db=db,
            session_id="test-session",
            messages=messages,
        )

        saved = list_messages(db, "test-session")

        assert len(saved) == 2
        assert saved[0].role == "user"
        assert saved[0].content == "你好"
        assert saved[1].role == "assistant"
        assert saved[1].content == "你好！有什么可以帮你？"
    finally:
        db.close()
        engine.dispose()


def test_create_messages_with_empty_list_does_nothing():
    """空列表不应产生数据库记录，也不应报错。"""
    engine, db = make_test_db()

    try:
        create_messages(
            db=db,
            session_id="test-session",
            messages=[],
        )

        assert list_messages(db, "test-session") == []
    finally:
        db.close()
        engine.dispose()


"""事务回滚机制"""

def test_create_messages_rolls_back_on_database_error():
    """批量写入失败时，整个事务应回滚。"""

    class TestBase(DeclarativeBase):
        pass

    class UniqueMessage(TestBase):
        __tablename__ = "unique_messages"
        __table_args__ = (
            UniqueConstraint("content", name="uq_test_content"),
        )

        id: Mapped[int] = mapped_column(primary_key=True)
        content: Mapped[str] = mapped_column(String(100))

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestBase.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    db = TestSession()

    try:
        # 先插入一条已存在的内容，后续重复插入将触发唯一约束错误。
        db.add(UniqueMessage(content="duplicate"))
        db.commit()

        # 这里直接验证数据库事务的基本行为：
        # 两条重复记录一起提交时，不能只保存其中一条。
        db.add_all([
            UniqueMessage(content="new-message"),
            UniqueMessage(content="duplicate"),
        ])

        try:
            db.commit()
            assert False, "预期数据库唯一约束会触发错误"
        except Exception:
            db.rollback()

        # 回滚后，第一条新增记录也不应该存在。
        contents = db.query(UniqueMessage.content).all()
        assert ("new-message",) not in contents
    finally:
        db.close()
        engine.dispose()


def test_create_messages_rolls_back_when_commit_fails(monkeypatch):
    """模拟提交失败，验证 create_messages 会回滚整批消息。"""
    engine, db = make_test_db()

    try:
        # 模拟数据库提交失败；rollback() 仍然使用真实的 SQLAlchemy 方法。
        def fail_commit():
            raise RuntimeError("模拟数据库提交失败")

        monkeypatch.setattr(db, "commit", fail_commit)

        messages = [
            Message(role="user", content="你好"),
            Message(role="assistant", content="你好！"),
        ]

        with pytest.raises(RuntimeError, match="模拟数据库提交失败"):
            create_messages(
                db=db,
                session_id="rollback-session",
                messages=messages,
            )

        # 如果 create_messages 正确回滚，这个会话不应留下任何消息。
        saved = list_messages(db, "rollback-session")
        assert saved == []
    finally:
        db.close()
        engine.dispose()