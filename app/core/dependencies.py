from app.chat_serivce import ChatService


# 服务启动请求了一次就不在启动了
def get_chat_service()->ChatService:

    return ChatService()