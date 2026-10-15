import logging

from openai import OpenAI

from app.core.config import  settings
from app.exceptions.custom import LLMException


# 工程思想：配置与代码分离
class LLMClient:
    def __init__(self):
        self.api_key=settings.DASHSCOPE_API_KEY
        self.api_url=settings.DASHSCOPE_BASE_URL
        self.model=settings.MODEL_NAME

        self.client=OpenAI(
            api_key=self.api_key,
            base_url=self.api_url,
            timeout=60.0,
            max_retries=2
        )
    def chat(self,messages)->str:
        """发送消息列表并返回模型回答"""

        # Message转换为SDK所需的字典
        formatted_messages=[
            message.model_dump()
            if hasattr(message,"model_dump")
            else message
            for message in messages
        ]

        try:
            response=self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
            )
            answer=response.choices[0].message.content

            if not answer or not answer.strip():
                raise LLMException(
                    code=5001,
                    message="模型返回了空回答"
                )
            return answer.strip()
        except LLMException:
            raise
        except Exception as exc:
            logging.exception("调用通义千问模型失败")
            raise LLMException(
                code=5002,
                message="模型服务调用失败，请稍后重试"
            )from exc