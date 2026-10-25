
import pytest
from fastapi.testclient import TestClient

from main import app
from app.core.dependencies import get_chat_service
from app.exceptions.custom import LLMException

class FakeChatService:
    """模拟 ChatService，不会调用真实模型"""

    def chat(self, messages,session_id=None):
        return "你好，我是 AI 助手。"


class FailedChatService:
    """模拟模型调用失败"""

    def chat(self, messages,session_id=None):
        raise LLMException(
            code=5002,
            message="模型服务调用失败，请稍后重试",
        )


@pytest.fixture
def client():
    """每个测试使用独立的依赖覆盖配置"""

    app.dependency_overrides[get_chat_service] = (
        lambda: FakeChatService()
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_chat_success(client):
    """测试正常聊天请求"""

    response = client.post(
        "/chat",
        json={
            "messages": [
                {
                    "role": "user",
                    "content": "你好",
                }
            ]
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["code"] == 0
    assert body["data"]["answer"] == "你好，我是 AI 助手。"
    assert body["trace_id"]
    print("响应头",dict(response.headers))
    print("响应体",response.json())
    assert response.headers["X-Trace-ID"] == body["trace_id"]
    assert response.headers["X-Request-ID"]==body["trace_id"]




def test_chat_empty_messages(client):
    """测试空消息列表"""

    response = client.post(
        "/chat",
        json={"messages": []},
    )

    assert response.status_code == 422


def test_chat_invalid_role(client):
    """测试不支持的消息角色"""

    response = client.post(
        "/chat",
        json={
            "messages": [
                {
                    "role": "human",
                    "content": "你好",
                }
            ]
        },
    )

    assert response.status_code == 422


def test_chat_llm_exception():
    """测试 LLMException 被全局处理器转换"""

    app.dependency_overrides[get_chat_service] = (
        lambda: FailedChatService()
    )

    try:
        with TestClient(app) as test_client:
            response = test_client.post(
                "/chat",
                json={
                    "messages": [
                        {
                            "role": "user",
                            "content": "你好",
                        }
                    ]
                },
            )

        assert response.status_code == 502

        body = response.json()
        assert body["code"] == 5002
        # assert "trace_id" in body
        assert body["trace_id"]
        assert response.headers["X-Trace-ID"] == body["trace_id"]
        assert response.headers["X-Request-ID"] == body["trace_id"]
    finally:
        app.dependency_overrides.clear()
