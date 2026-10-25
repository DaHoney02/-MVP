
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base
from app.db.models import MessageRecord
from app.db.message_repository import (
    create_message,
    delete_message,
    get_message,
    list_messages,
    update_message,
)


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )
    Base.metadata.create_all(bind=engine)

    with TestingSession() as session:
        yield session

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_create_and_get_message(db):
    created = create_message(
        db, "session_a", "user", "什么是 RAG？"
    )

    assert created.id is not None
    assert created.content == "什么是 RAG？"

    found = get_message(db, created.id)
    assert found is not None
    assert found.session_id == "session_a"


def test_list_messages_isolated_by_session(db):
    create_message(db, "session_a", "user", "问题 A")
    create_message(db, "session_a", "assistant", "回答 A")
    create_message(db, "session_b", "user", "问题 B")

    messages = list_messages(db, "session_a")

    assert len(messages) == 2
    assert all(m.session_id == "session_a" for m in messages)


def test_update_message(db):
    message = create_message(
        db, "session_a", "assistant", "旧回答"
    )

    updated = update_message(db, message.id, "新回答")

    assert updated is not None
    assert updated.content == "新回答"


def test_delete_message(db):
    message = create_message(
        db, "session_a", "user", "待删除"
    )

    assert delete_message(db, message.id) is True
    assert get_message(db, message.id) is None
    assert delete_message(db, message.id) is False


def test_update_missing_message_returns_none(db):
    assert update_message(db, 99999, "新内容") is None
