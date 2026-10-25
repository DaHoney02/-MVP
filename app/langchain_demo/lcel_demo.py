

"""
demo:LCEL链
运行方式：python -m app.lcel_demo
"""
import asyncio

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.core.config import settings


def build_chain():
    """组装提示词、模型和输出解析器，返回可执行的链"""
    prompt=ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是一名耐心的AI应用开发导师。"
                "请用中文解释技术问题，并尽量各处具体例子"
            ),
            ("human","{question}"),
        ]
    )

    #2.创建模型组件
    model=ChatOpenAI(
        api_key=settings.DASHSCOPE_API_KEY,
        base_url=settings.DASHSCOPE_BASE_URL,
        model=settings.MODEL_NAME,
        temperature=0.7
    )

    #3.模型返回的消息内容解析为普通字符串
    parser=StrOutputParser()

    #4.LCEL链
    chain=prompt | model | parser

    return chain

def main():
    # """执行链，查看完整输入输出过程"""
    # chain=build_chain()
    # result=chain.invoke(
    #     {"question":"什么是RAG?,请用一个通俗易懂的例子说明"}
    # )
    # print("模型回答：",result)

    """同步完整输出和同步流式输出"""
    chain=build_chain()
    inputs={"question":"请用三句话解释什么是fastAPI"}
    print("+++++++方式一：invoke：完整输出+++++++")
    result=chain.invoke(inputs)
    print("结果",result)

    print("++++++++stream:流式输出+++++++")
    for chunk in chain.stream(inputs):
        print(chunk,end="",flush=True)
    print()

async def async_demo():
    """异步的完整输出和流式输出"""
    chain=build_chain()
    inputs={"question":"请用三句话解析什么是RAG"}

    result=await chain.ainvoke(inputs)
    print("异步完整输出：",result)

    async for chunk in chain.astream(inputs):
        print(chunk,end="",flush=True)
    print()

if __name__=="__main__":
    main()
    asyncio.run(async_demo())

