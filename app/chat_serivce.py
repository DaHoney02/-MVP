import logging

from app.llm_client import LLMClient
from app.schemas.schemas import Message

logger=logging.getLogger(__name__)

class ChatService:
    """聊天业务服务"""
    def __init__(self):
        self.llm_client=LLMClient()

    def chat(self,messages:list[Message])->str:
        """接收用户问题，调用LLM,并返回回答"""

        if not messages:
            raise ValueError("聊天消息列表不能为空")

        logger.info(f"开始处理问题:{messages}")

        answer = self.llm_client.chat(messages)

        if answer is None or not answer.strip():
            logger.warning("模版返回了空回答")
            raise RuntimeError("模型未返回有效回答" )

        return answer.strip()