
"""
单独测试 DashScope Embedding 接口。

运行：
    python -m app.test_embedding

目的：
    暂时绕过 LangChain 和向量库，直接验证底层 API。
"""

from openai import OpenAI
from app.core.config import settings


def main():
    client = OpenAI(
        api_key=settings.DASHSCOPE_API_KEY,
        base_url=settings.DASHSCOPE_BASE_URL,
    )

    response = client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input="RAG 是检索增强生成。",
        encoding_format="float",
    )

    # 向量通常是一组浮点数；这里只打印维度和前 5 个数。
    vector = response.data[0].embedding

    print("Embedding 调用成功")
    print("模型：", response.model)
    print("向量维度：", len(vector))
    print("前 5 个数：", vector[:5])


if __name__ == "__main__":
    main()
