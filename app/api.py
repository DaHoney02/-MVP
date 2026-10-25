

"""接口文件：接收请求-参数校验-调用Service-返回结果"""
import json
import logging

from fastapi import APIRouter, Depends,Request
from starlette.responses import StreamingResponse

from app.chat_service import ChatService
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

    answer=chat_service.chat(
        request.messages,
        session_id=request.session_id
    )

    return  ResponseModel[ChatResponse](
        trace_id=http_request.state.trace_id,
        data=ChatResponse(answer=answer)
    )

@router.post("/chat/stream")  #注册一个post接口
def chat_stream(
        request:ChatRequest,
        http_request:Request,
        chat_service:ChatService=Depends(get_chat_service)
):
    """以SSE方式流式返回模型回答"""
    # ttp_request.state---请求级上下文存储(中间件一般在请求进来时生成trace_id放到state，用于全链路追踪)
    trace_id=http_request.state.trace_id
    def event_stream():
        stream=chat_service.chat_stream(
            request.messages,
            session_id=request.session_id
        )
        try:
            # 迭代大模型流式分片
            for content in stream:
                payload=json.dumps(
                    {
                        "trace_id":trace_id,
                        "content":content
                    },
                    ensure_ascii=False  #json中的中文直接显示
                )
                # json内容包装成sse消息
                yield f"data: {payload}\n\n"  #SSE协议格式 事件结束  （规范：data: 消息内容\n\n）
            #     [DONE]---流正常结束标记
            yield "data: [DONE]\n\n"

        except Exception:
            logging.getLogger(__name__).exception(
                "流式输出失败trace_id=%s",trace_id
            )

            payload=json.dumps(
                {
                    "trace_id": trace_id,
                    "error": "模型生成失败，请稍后重试",
                },
                ensure_ascii=False,
            )
            # event: error---自定义SSE事件类型  注意data: 后面有空格
            yield f"event: error\ndata: {payload}\n\n"

        # 负责尝试关闭服务层生成器
        finally:
            close=getattr(stream,"close",None) #尝试获取生成器的close方法，若没有，则返回None
            if callable(close): #检查拿到的对象是否能调用
                close()

            logging.getLogger(__name__).info(
                "SSE流结束 trace_id=%s", trace_id
            )

    #         StreamingResponse()：返回流式相应的Response
    return StreamingResponse(
        event_stream(),  #迭代的生成器
        media_type="text/event-stream",  #告诉浏览器，这是SSE长连接流【必填】
        headers={
            "Cache-Control":"no-cache",  #禁止浏览器缓存SSE流【必填】
            "X-trace-ID":trace_id,
            "X-Request-ID":trace_id
        }

    )

