import json

from fastapi.testclient import TestClient
from main import app
from app.core.dependencies import get_chat_service

class FakeChatService:
    """模拟聊天服务，不调用真实大模型"""

    def chat_stream(self, messages,session_id):
        yield "你好"
        yield "，世界！"

class FakeErrorChatService:
    """模拟流式生成过程中发生异常"""

    def chat_stream(self, messages,session_id):
        yield "部分回答"
        raise RuntimeError("模拟模型调用失败")


def test_chat_stream_success():
    app.dependency_overrides[get_chat_service] = (
        lambda: FakeChatService()
    )

    try:
        with TestClient(app) as client:
            response = client.post(
                "/chat/stream",
                json={
                    "messages": [
                        {"role": "user", "content": "你好"}
                    ]
                },
            )

        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        assert response.headers["x-trace-id"]
        assert (
            response.headers["x-trace-id"]
            == response.headers["x-request-id"]
        )

        body = response.text

        assert '"content": "你好"' in body
        assert '"content": "，世界！"' in body
        assert "data: [DONE]" in body

    finally:
        app.dependency_overrides.pop(get_chat_service, None)

def test_chat_stream_error():
    app.dependency_overrides[get_chat_service] = (
        lambda: FakeErrorChatService()
    )

    try:
        with TestClient(app) as client:
            response = client.post(
                "/chat/stream",
                json={
                    "messages": [
                        {"role": "user", "content": "你好"}
                    ]
                },
            )

        assert response.status_code == 200
        assert "部分回答" in response.text
        assert "event: error" in response.text
        assert "模型生成失败" in response.text

    finally:
        app.dependency_overrides.pop(get_chat_service, None)

def test_chat_stream_generator_close():
    """验证客户端关闭流后，生成器通知继续迭代"""
    closed=[]
    def fake_stream(messages):
        try:
            yield "第一段"
            yield "第二段"
        finally:
            closed.append(True)

    class FakeCloseService:
        def chat_stream(self,messages):
            return fake_stream(messages)

    service=FakeCloseService()
    stream=service.chat_stream([])

    assert next(stream)=="第一段"
    stream.close()
    assert closed==[True]


def test_chat_stream_api_closes_service_stream():
    """验证 API 层在响应结束时会关闭 Service 返回的流"""
    streams = []

    class FakeStream:
        def __init__(self):
            self.chunks = iter(["第一段", "第二段"])
            self.closed = False

        def __iter__(self):
            return self

        def __next__(self):
            return next(self.chunks)

        def close(self):
            self.closed = True

    class FakeCloseChatService:
        def chat_stream(self, messages, session_id=None):
            stream = FakeStream()
            streams.append(stream)
            return stream

    app.dependency_overrides[get_chat_service] = (
        lambda: FakeCloseChatService()
    )

    try:
        with TestClient(app) as client:
            response = client.post(
                "/chat/stream",
                json={
                    "messages": [
                        {"role": "user", "content": "测试关闭"}
                    ]
                },
            )

        assert response.status_code == 200
        assert "data: [DONE]" in response.text

        # 确认 API 层关闭了 Service 返回的流
        assert len(streams) == 1
        assert streams[0].closed is True

    finally:
        app.dependency_overrides.pop(get_chat_service, None)
