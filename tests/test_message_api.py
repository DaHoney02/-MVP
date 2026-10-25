from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.db.message_api import message_router
from fastapi import FastAPI


def test_message_api_persists_data():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine)

    Base.metadata.create_all(bind=engine)

    test_app = FastAPI()
    test_app.include_router(message_router)

    def override_get_db():
        with TestingSession() as db:
            yield db

    test_app.dependency_overrides[get_db] = override_get_db
    client = TestClient(test_app)

    try:
        response = client.post(
            "/messages",
            json={
                "session_id": "test_session",
                "role": "user",
                "content": "测试持久化",
            },
        )

        assert response.status_code == 200
        saved = response.json()
        assert saved["content"] == "测试持久化"
        assert saved["id"] > 0

        query = client.get(
            "/sessions/test_session/messages"
        )
        assert query.status_code == 200
        assert len(query.json()) == 1
        assert query.json()[0]["id"] == saved["id"]
    finally:
        client.close()
        test_app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()