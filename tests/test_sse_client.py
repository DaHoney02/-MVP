import json
import sys

import requests


URL = "http://127.0.0.1:8000/chat/stream"

# 必须与 app/schemas/schemas.py 中的 ChatRequest 结构一致
PAYLOAD = {
    "messages": [
        {
            "role": "user",
            "content": "你好，请用五句话介绍一下fastapi。",
        }
    ]
}


def main():
    print("=" * 50)
    print("开始请求 SSE 流式接口")
    print(f"请求地址：{URL}")
    print("=" * 50)

    try:
        with requests.post(
            URL,
            json=PAYLOAD,
            stream=True,
            timeout=(10, 120),
            headers={"Accept": "text/event-stream"},
        ) as response:

            print(f"HTTP 状态码：{response.status_code}")
            print(f"Content-Type：{response.headers.get('Content-Type')}")
            print(f"Trace ID：{response.headers.get('X-Trace-ID')}")

            # 先处理 HTTP 层错误，输出 FastAPI 返回的详细校验信息
            if not response.ok:
                print("\n请求失败，服务端返回：")
                print(response.text)
                response.raise_for_status()

            content_type = response.headers.get("Content-Type", "")
            if "text/event-stream" not in content_type:
                print("\n警告：响应类型不是 text/event-stream")
                print(response.text)
                return

            print("\n开始接收流式内容：\n")

            event_name = "message"
            data_lines = []
            received_done = False
            received_error = False

            # iter_lines---逐行接收SSE数据
            for line in response.iter_lines(decode_unicode=True):
                if line is None:
                    continue

                # SSE 使用空行表示一个事件结束
                if line == "":
                    if not data_lines:
                        event_name = "message"
                        continue

                    data = "\n".join(data_lines)

                    if data == "[DONE]":
                        print("\n\n[流式响应正常结束]")
                        received_done = True
                    elif event_name == "error":
                        print(f"\n\n[服务端错误事件] {data}")
                        received_error = True
                    else:
                        try:
                            payload = json.loads(data)

                            if payload.get("error"):
                                print(f"\n\n[生成失败] {payload['error']}")
                                received_error = True
                            elif "content" in payload:
                                # 实时打印每一段文本，不额外换行
                                print(payload["content"], end="", flush=True)
                            else:
                                print(f"\n[其他事件] {payload}")

                        except json.JSONDecodeError:
                            print(f"\n[无法解析的 SSE 数据] {data}")

                    data_lines = []
                    event_name = "message"
                    continue

                # 解析 SSE 字段
                if line.startswith("event:"):
                    event_name = line[len("event:"):].strip()
                elif line.startswith("data:"):
                    value = line[len("data:"):].lstrip(" ")
                    data_lines.append(value)

            if received_error:
                print("验收失败：服务端返回错误事件")
                sys.exit(1)

            if not received_done:
                print("验收失败：未收到[DONE],流可能异常中断")
                sys.exit(1)
            print("\n验收通过：收到完整的sse流式响应")

            if received_error:
                sys.exit(1)

    except requests.exceptions.ConnectionError:
        print("\n连接失败：请确认 FastAPI 服务已启动，且端口为 8000。")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("\n请求超时：请检查模型响应时间或服务端是否卡住。")
        sys.exit(1)
    except requests.exceptions.HTTPError:
        print("\nHTTP 请求失败，请根据上方服务端响应内容检查请求参数。")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n用户手动中断请求。")


if __name__ == "__main__":
    main()