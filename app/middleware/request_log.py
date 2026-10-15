import logging
import time
import uuid

from fastapi import Request

logger=logging.getLogger(__name__)


# 统一请求日志规则
async def request_log_middleware(
        request:Request,
        call_next
):
    # 为本次请求生成唯一追踪ID
    trace_id=uuid.uuid4().hex
    request.state.trace_id=trace_id  #将ID存入当前请求的状态对象

    start_time=time.perf_counter()
    response=None
    try:
        # 2.记录请求开始
        logger.info(
            "请求开始 trace_id=%s method=%s path=%s",
            trace_id,
            request.method,
            request.url.path
        )
        # 3.交给后续中间件和接口处理
        response=await call_next(request)
        # 4.将同一个ID写入响应头
        response.headers["X-Trace-ID"] = trace_id
        # 兼容X-Request-ID的客户端
        response.headers["X-Request-ID"]=trace_id

        return response

    except Exception:
        #5.记录未被异常处理接管的异常，并继续抛出、
        logger.exception("请求异常 trace_id=%s",trace_id)
        raise

    finally:
        # perf_counter()---测试耗时
        cost_ms=(time.perf_counter()-start_time) *1000

        status_code=(
            response.status_code if response is not None else 500
        )
        logger.info(
            "请求结束 trace_id=%s method=%s path=%s "
            "status_code=%s duration_ms=%.2f",
            trace_id,
            request.method,
            request.url.path,
            status_code,
            cost_ms
        )
