
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.chat_service import ChatService
from app.db.database import Base
from app.db.message_repository import list_chat_messages
from app.db.models import MessageRecord
from app.schemas.schemas import Message


class FakeLLMClient:
    """模拟大模型，避免测试依赖真实 API 和网络。"""

    def __init__(self):
        self.chat_calls = []
        self.stream_calls = []

    def chat(self, messages):
        # 保存模型实际收到的上下文，方便断言历史记忆。
        self.chat_calls.append(list(messages))
        return "你正在学习 Python。"

    def chat_stream(self, messages):
        self.stream_calls.append(list(messages))
        yield "你正在学习 "
        yield "Python。"


@pytest.fixture
def db_session():
    """创建独立的内存 SQLite 数据库，测试后释放资源。"""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    TestingSession = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )
    db: Session = TestingSession()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_chat_saves_messages_and_reuses_history(db_session):
    """普通聊天：保存本轮消息，并在下一轮读取历史。"""
    service = ChatService(db=db_session)
    fake_llm = FakeLLMClient()
    service.llm_client = fake_llm

    first_answer = service.chat(
        messages=[
            Message(role="user", content="我正在学习 Python。")
        ],
        session_id="memory_test",
    )

    assert first_answer == "你正在学习 Python。"

    # 数据库里应有第一轮的用户消息和助手回答。
    history = list_chat_messages(db_session, "memory_test")
    assert [item.role for item in history] == ["user", "assistant"]
    assert history[0].content == "我正在学习 Python。"

    # 第二轮使用同一个 session_id，验证模型收到旧历史。
    service.chat(
        messages=[
            Message(role="user", content="我正在学习什么？")
        ],
        session_id="memory_test",
    )

    second_context = fake_llm.chat_calls[1]
    assert any(
        item.content == "我正在学习 Python。"
        for item in second_context
    )
    assert any(
        item.content == "我正在学习什么？"
        for item in second_context
    )

    # 两轮对话，每轮各有一条用户消息和一条助手回答。
    records = db_session.scalars(
        select(MessageRecord)
        .where(MessageRecord.session_id == "memory_test")
        .order_by(MessageRecord.id)
    ).all()
    assert len(records) == 4


def test_stream_chat_saves_complete_answer(db_session):
    """流式聊天：分片输出，但数据库只保存完整助手回答。"""
    service = ChatService(db=db_session)
    fake_llm = FakeLLMClient()
    service.llm_client = fake_llm

    chunks = list(
        service.chat_stream(
            messages=[
                Message(role="user", content="测试流式记忆")
            ],
            session_id="stream_test",
        )
    )

    assert chunks == ["你正在学习 ", "Python。"]

    history = list_chat_messages(db_session, "stream_test")
    assert len(history) == 2
    assert history[0].role == "user"
    assert history[1].role == "assistant"
    assert history[1].content == "你正在学习 Python。"
