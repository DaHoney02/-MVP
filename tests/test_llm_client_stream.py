from types import SimpleNamespace
from unittest.mock import MagicMock

from app.llm_client import LLMClient
from app.schemas.schemas import Message


def test_chat_stream_converts_messages_and_closes_response():
    """验证消息格式转换，以及流中途关闭时底层响应会被关闭"""

    chunk=SimpleNamespace(
        choices=[
            SimpleNamespace(
                delta=SimpleNamespace(content="你好")
            )
        ]
    )

    # 模拟底层流式响应及其上下文管理器
    response=MagicMock()
    response.__iter__.return_value=iter([chunk])

    stream_context=MagicMock()
    stream_context.__enter__.return_value=response

    # 创建客户端，但不发起真实网络请求
    llm_client=LLMClient()
    llm_client.client=MagicMock()
    llm_client.client.chat.completions.create.return_value=stream_context

    messages=[
        Message(role="user",content="你好")
    ]

    # 启动生成器,读取第一个文本片段
    stream=llm_client.chat_stream(messages)
    assert next(stream)=="你好"

    #用户中途停止接收
    stream.close()

    # 验证发给SDK的消息已转换为dict
    call_kwargs=(
        llm_client.client.chat.completions.create.call_args.kwargs
    )
    assert  call_kwargs["messages"]==[
        {"role":"user","content":"你好"}
    ]
    assert call_kwargs["stream"] is True

    # 验证底层响应的上下文管理器已退出
    stream_context.__exit__.assert_called_once()
