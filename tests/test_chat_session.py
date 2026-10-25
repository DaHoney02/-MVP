
from app.chat_service import ChatService
from app.schemas.schemas import Message
from app.seession_store import session_store, MAX_HISTORY_MESSAGES


class FakeLLMClient:
    """模拟模型调用，记录每次收到的消息"""

    def __init__(self):
        self.calls=[]

    def chat(self,messages):
        self.calls.append(list(messages))
        return f"模拟回答{len(self.calls)}"

def test_chat_remember_previous_turn(monkeypatch):
    session_id="test_session_history"
    session_store.save_messages(session_id,[])

    service=ChatService()
    fake_llm=FakeLLMClient()
    monkeypatch.setattr(service,"llm_client",fake_llm)

    # 第一轮对话
    answer1=service.chat(
        [Message(role="user",content="我叫小明")],
        session_id=session_id
    )
    assert answer1=="模拟回答1"

    # 第二轮只传本轮新消息
    answer2 = service.chat(
        [Message(role="user", content="我叫什么？")],
        session_id=session_id,
    )
    assert answer2 == "模拟回答2"

    second_call = fake_llm.calls[1]

    # 第二次模型调用应包含上一轮用户消息、助手回答和本轮新消息
    assert [m.content for m in second_call] == [
        "我叫小明",
        "模拟回答1",
        "我叫什么？",
    ]

def test_different_sessions_are_isolated(monkeypatch):
    session_a = "test-isolation-a"
    session_b = "test-isolation-b"
    session_store.save_messages(session_a, [])
    session_store.save_messages(session_b, [])

    service = ChatService()
    fake_llm = FakeLLMClient()
    monkeypatch.setattr(service, "llm_client", fake_llm)

    service.chat(
        [Message(role="user", content="A 的私有消息")],
        session_id=session_a,
    )
    service.chat(
        [Message(role="user", content="B 的私有消息")],
        session_id=session_b,
    )

    # B 的模型请求不能包含 A 的消息
    second_call = fake_llm.calls[1]
    contents = [m.content for m in second_call]

    assert "B 的私有消息" in contents
    assert "A 的私有消息" not in contents



def test_session_history_is_limited():
    session_id = "test-history-limit"

    messages = [
        Message(role="user", content=f"消息{i}")
        for i in range(MAX_HISTORY_MESSAGES + 5)
    ]

    session_store.save_messages(session_id, messages)

    saved = session_store.get_messages(session_id)

    assert len(saved) == MAX_HISTORY_MESSAGES
    assert saved[0].content == "消息5"
    assert saved[-1].content == f"消息{MAX_HISTORY_MESSAGES + 4}"

def test_trim_messages_preserves_system_prompt():
    session_id="test-system-prompt"
    messages=[
        Message(role="system",content="你是一个专业的ai助手"),
    ]+[
        Message(role="user",content=f"问题{i}")
        for i in range(MAX_HISTORY_MESSAGES+5)
    ]
    session_store.save_messages(session_id,messages)
    saved=session_store.get_messages(session_id)

    assert saved[0].role=="system"
    assert saved[0].content=="你是一个专业的ai助手"
    assert len(saved)==MAX_HISTORY_MESSAGES+1
    assert saved[1].content=="问题5"

def test_trim_messages_does_not_start_with_assistant():
    messages = [
        Message(role="assistant", content="较早的回答"),
        Message(role="user", content="最近的问题"),
        Message(role="assistant", content="最近的回答"),
    ]

    trimmed = session_store.trim_messages(messages)

    assert trimmed[0].role == "user"
    assert trimmed[0].content == "最近的问题"


def test_chat_stream_remembers_previous_turn(monkeypatch):
    session_id = "test-stream-session"
    session_store.save_messages(session_id, [])

    service = ChatService()

    class FakeStreamLLMClient:
        def __init__(self):
            self.calls = []

        def chat_stream(self, messages):
            self.calls.append(list(messages))
            yield "模拟"
            yield "流式回答"

    fake_llm = FakeStreamLLMClient()
    monkeypatch.setattr(service, "llm_client", fake_llm)

    # 第一轮：消费完整流
    chunks1 = list(
        service.chat_stream(
            [Message(role="user", content="记住关键词：蓝鲸")],
            session_id=session_id,
        )
    )
    assert "".join(chunks1) == "模拟流式回答"

    # 第二轮：验证历史已被保存并传给模型
    chunks2 = list(
        service.chat_stream(
            [Message(role="user", content="关键词是什么？")],
            session_id=session_id,
        )
    )
    assert "".join(chunks2) == "模拟流式回答"

    second_call = fake_llm.calls[1]
    contents = [message.content for message in second_call]

    assert "记住关键词：蓝鲸" in contents
    assert "模拟流式回答" in contents
    assert "关键词是什么？" in contents

# 验证：流式回答只输出一部分就被关闭时，底层生成器会被清理，而且不完整回答不会保存到会话中。

def test_chat_stream_close_does_not_save_incomplete_answer(monkeypatch):
    """提前关闭流式生成器时，应关闭底层流且不保存不完整回答"""
    session_id = "test-stream-cancel"
    session_store.save_messages(session_id, [])

    service = ChatService()

    # 记录底层生成器是否执行了清理逻辑
    state = {"closed": False}

    class FakeStreamLLMClient:
        def chat_stream(self, messages):
            try:
                yield "你好"
                yield "，世界"
            finally:
                state["closed"] = True

    monkeypatch.setattr(
        service,
        "llm_client",
        FakeStreamLLMClient(),
    )

    # 记录会话保存操作
    save_calls = []
    original_save = session_store.save_messages

    def track_save(sid, messages):
        save_calls.append((sid, list(messages)))
        original_save(sid, messages)

    monkeypatch.setattr(
        session_store,
        "save_messages",
        track_save,
    )

    # 启动流式回答，只读取第一段
    stream = service.chat_stream(
        [Message(role="user", content="测试中途关闭")],
        session_id=session_id,
    )

    first_chunk = next(stream)
    assert first_chunk == "你好"

    # 模拟调用方中途取消
    stream.close()

    # 断言 1：底层生成器的 finally 已执行
    assert state["closed"] is True

    # 断言 2：不完整回答没有被保存
    assert save_calls == []

    # 断言 3：会话历史仍然为空
    assert session_store.get_messages(session_id) == []

def test_trim_message_preserves_complete_recent_turns():
    """历史裁剪后保留最近的完整问答轮次"""
    messages=[]

    # 构建12轮完整对话，共24条消息
    for i in range(MAX_HISTORY_MESSAGES // 2+2):
        messages.append(
            Message(role="user",content=f"用户问题{i}")
        )
        messages.append(
            Message(role="assistant",content=f"助手回答{i}")
        )
    trimmed=session_store.trim_messages(messages)

    assert len(trimmed)==MAX_HISTORY_MESSAGES

    assert trimmed[0].role=="user"
    assert trimmed[0].content=="用户问题2"
    assert trimmed[-1].role=="assistant"
    assert trimmed[-1].content=="助手回答11"

    # 确保每轮的角色顺序都是user->assistant
    for i in range(0,len(trimmed),2):
        assert trimmed[i].role=="user"
        assert trimmed[i+1].role=="assistant"
