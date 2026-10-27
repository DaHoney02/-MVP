
from fastapi import FastAPI,Request
from starlette.responses import JSONResponse

from app.core.lifespan import lifespan
from app.api import router as chat_router
from app.core.logger import setup_logger
from app.db.message_api import message_router
from app.exceptions.custom import LLMException
from app.middleware.request_log import request_log_middleware
from app.db.aftercare_api import router as aftercare_router

logger=setup_logger()

# 创建fastapi应用对象
app=FastAPI(
    title="AI assistant API",
    description="基于通义千问的ai后端接口",
    version="0.1.0",
    lifespan=lifespan  #生命周期
)
# 注册路由
app.include_router(chat_router)  #把子路由chat_router挂载到主app
app.include_router(message_router)
app.include_router(aftercare_router)

@app.get("/")
def home():
    return {"message":"AI API 服务也开启"}

@app.get("/health")
def health():
    return {"status":"ok"}

# 全局异常处理(统一)
@app.exception_handler(LLMException)
async def llm_exception_handler(request:Request,exc:LLMException):
    return JSONResponse(
        status_code=502,
        content={
            "code":exc.code,
            "message":exc.message,
            # request.state--在http请求处理过程中保存临时数据
            "trace_id":getattr(request.state,"trace_id",None),
        },
        headers = {
            "X-Trace-ID": getattr(request.state, "trace_id", ""),
            "X-Request-ID": getattr(request.state, "trace_id", ""),
        },
    )

# 注册Middleware
app.middleware("http")(request_log_middleware)  # 所有接口自动记录
