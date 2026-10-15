

"""接口文件：接收请求-参数校验-调用Service-返回结果"""
from fastapi import APIRouter, Depends,Request

from app.chat_serivce import ChatService
from app.core.dependencies import get_chat_service
from app.schemas.response import ResponseModel
from app.schemas.schemas import ChatResponse, ChatRequest

router=APIRouter()  #创建子路由对象router


@router.post(
    "/chat",
    response_model=ResponseModel[ChatResponse])
def chat(
        request:ChatRequest,
        http_request:Request,
        chat_service:ChatService=Depends(get_chat_service)
):
    """处理聊天请求"""

    answer=chat_service.chat(request.messages)

    return  ResponseModel[ChatResponse](
        trace_id=http_request.state.trace_id,
        data=ChatResponse(answer=answer)
    )