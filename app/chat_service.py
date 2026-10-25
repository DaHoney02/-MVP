import logging
from typing import Iterator
from sqlalchemy.orm import Session

from app.db.message_repository import list_chat_messages, create_messages
from app.llm_client import LLMClient
from app.schemas.schemas import Message
from app.seession_store import session_store

logger=logging.getLogger(__name__)

class ChatService:
    """聊天业务服务"""
    def __init__(self,db:Session | None=None):
        self.llm_client=LLMClient()
        self.db=db

    def chat(
            self,
            messages:list[Message],
            session_id:str|None=None
    )->str:
        """接收用户问题，调用LLM,并返回回答"""
        if not messages:
            raise ValueError("聊天消息列表不能为空")

        if session_id:
            if self.db is not None:
                # 生产API使用SQLite历史记录
                history=list_chat_messages(self.db,session_id)
            else:
                # 保留内存存储行为
                history=session_store.get_messages(session_id)

            full_messages=session_store.trim_messages(history+messages)  #拼接
        else:
            full_messages=messages

        answer = self.llm_client.chat(full_messages)

        if answer is None or not answer.strip():
            logger.warning("模版返回了空回答")
            raise RuntimeError("模型未返回有效回答" )

        answer=answer.strip()

        # 保存本轮对话
        if session_id:
            if self.db is not None:
                # 将本轮用户消息与ai回答合并成一个列表
                turn_messages=messages+[
                    Message(role="assistant",content=answer)
                ]
                # 一次调用批量保存，统一提交事务
                create_messages(
                    db=self.db,
                    session_id=session_id,
                    messages=turn_messages
                )
            else:
                # 保留内存存储行为
                session_store.save_messages(
                    session_id,
                    full_messages+[Message(
                        role="assistant",
                        content=answer
                        )
                    ],
                )
        return answer

    def chat_stream(
            self,
            messages:list[Message],
            session_id:str | None=None,
    )->Iterator[str]:
        """流式生成回答，并在回答完成后保存本轮对话"""

        if not messages:
            raise ValueError("聊天消息列表不能为空")

        # 1、读取历史记录：API注入数据库时使用SQLite；否则保留内存存储行为
        if session_id:
            if self.db is not None:
                history=list_chat_messages(self.db,session_id)
            else:
                history=session_store.get_messages(session_id)
            # 拼接历史消息和本轮消息，执行历史裁剪
            full_messages=session_store.trim_messages(
                history+messages
            )
        else:
            full_messages=messages

        logger.info(
            "开始处理流式聊天，消息数量=%s",
            len(messages)
        )

        #2.创建底层模型生成器，并准备收集完整回答
        answer_parts:list[str]=[]
        stream=self.llm_client.chat_stream(full_messages)

        # 默认认为生成没有正常完成
        completed=False

        try:
            for chunk in stream:
                if chunk:
                    answer_parts.append(chunk)  #加chunk保存
                    yield  chunk  #立即将当前chunk交给调用方，无需等整个回答生成【流式输出核心】
            completed=True
        finally:
            #4.无论正常结束、异常还是外部关闭，都尝试关闭底层模型流生层成器
            close=getattr(stream,"close",None)
            if callable(close):
                close()

        # 只有正常完成，且存有会话id，才保存本轮对话
        if completed and session_id:
            answer="".join(answer_parts).strip()

        # 5.只有正常生成关闭后，才保存本轮对话
        if session_id:
            answer="".join(answer_parts).strip()

            # 空回答不存入历史
            if answer:
                if self.db is not None:
                    turn_message=messages+[
                        Message(role="assistant",content=answer)
                    ]

                    create_messages(
                        db=self.db,
                        session_id=session_id,
                        messages=turn_message
                    )

                else:
                    session_store.save_messages(
                        session_id,
                        full_messages+[Message(
                            role="assistant",content=answer
                        )]
                    )