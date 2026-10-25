from threading import Lock

from app.schemas.schemas import Message

# session_id:区分不同对话
# Lock: 线程锁（在两个请求同时修改一个会话时，子让一个线程执行受保护的临界区），避免多个请求同时读写内存时发生竞争

MAX_HISTORY_MESSAGES = 20

class SessionStore:
    """内存会话存储，按session_id保存聊天历史"""
    def __init__(self):
        self._sessions:dict[str,list[Message]]={}
        self._lock=Lock()


    @staticmethod
    def trim_messages(messages:list[Message])->list[Message]:
        """保留系统提示词，并尽量从完整的用户对话轮次开始剪裁"""
        # 1.系统prompt单独保留，不计入普通历史条数
        system_messages=[
            message for message in messages
            if message.role=="system"
        ]

        #2.提取普通对话消息
        conversation = [
            message for message in messages
            if message.role != "system"
        ]
        #3.普通对话只保留最近MAX_HISTORY_MESSAGES
        conversation=conversation[-MAX_HISTORY_MESSAGES:]
        #4.若剪裁后以assistant开头，丢弃开头不完整的回答
        while conversation and conversation[0].role !="user":
            conversation.pop(0)

        return system_messages+conversation

    def get_messages(self,session_id:str)->list[Message]:
        with self._lock:
            messages=self._sessions.get(session_id,[])
            return list(messages)

    def save_messages(
            self,
            session_id:str,
            messages:list[Message],
    )-> None:
        with self._lock:
            self._sessions[session_id]=self.trim_messages(messages)

# 暴露SessionStore()出去
session_store=SessionStore()
