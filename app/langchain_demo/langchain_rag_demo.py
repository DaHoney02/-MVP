

"""
langchain与RAG：
设计流程：文档->切分->embedding->向量检索->将检索结果与问题做成prompt->模型回答
"""
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter


from app.core.config import settings

# 1.准备知识库
#Document  同时保存文本内容和元数据，便于后续追踪来源
RAG_DOCUMENTS=[
    Document(
        page_content=(
            "FastAPI 是一个 Python Web 框架，"
            "可以通过类型标注和 Pydantic 定义、校验请求数据。"
            "它支持异步接口，也可以使用依赖注入复用数据库连接等资源。"
        ),
        metadata={"source":"fastapi_noted"}
    ),
    Document(
        page_content=(
            "RAG 是检索增强生成。"
            "系统先从外部知识库检索与问题相关的文档，"
            "再把文档和用户问题一起交给大语言模型生成回答。"
            "RAG 可以为回答提供参考资料，但不能保证答案绝对正确。"
        ),
        metadata={"source": "rag_notes"},
    ),
    Document(
        page_content=(
            "Embedding 模型将文本转换为向量。"
            "向量检索可以依据向量相似度寻找相关文本。"
            "检索效果还受到切分方式、Embedding 模型和 Top-K 等因素影响。"
        ),
        metadata={"source": "embedding_notes"},
    ),
]

def format_docs(docs:list[Document])->str:
    """将检测到的多个Document整理为prompt可用的文本"""

    return "\n\n".join(
        f"来源：{doc.metadata.get('source','unknown')}\n"
        f"内容：{doc.page_content}"
        for doc in docs
    )

def build_rag_chain():
    """创建向量检索器和RAG问答链"""

    #2.文档切分
    #chunk_overlap:保留文本块重叠部分
    splitter=RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50
    )
    chunks=splitter.split_documents(RAG_DOCUMENTS)

    #3.配置embedding模型

    embeddings = OpenAIEmbeddings(
        api_key=settings.DASHSCOPE_API_KEY,
        base_url=settings.DASHSCOPE_BASE_URL,
        model=settings.EMBEDDING_MODEL,

        # 关键修复：
        # 不使用 LangChain 默认的长度检查与 token ID 输入处理，
        # 尽量将原始文本以字符串形式发送给兼容接口。
        check_embedding_ctx_length=False,
    )

    # 单独测试 LangChain 的 Embedding 调用
    print("模型：", settings.EMBEDDING_MODEL)
    print("地址：", settings.DASHSCOPE_BASE_URL)

    vector = embeddings.embed_query("RAG 是检索增强生成。")

    print("调用成功")
    print("向量维度：", len(vector))



    #4.文档转成向量并存入内存数据库
    vector_store=InMemoryVectorStore(embedding=embeddings)
    vector_store.add_documents(chunks)

    #5.创建检索器，每次取回最相关的3个文本块
    retriever=vector_store.as_retriever(
        search_kwargs={"k":3}
    )

    #6.构建聊天模型和提示词
    model=ChatOpenAI(
        api_key=settings.DASHSCOPE_API_KEY,
        base_url=settings.DASHSCOPE_BASE_URL,
        model=settings.MODEL_NAME,
        temperature=0
    )
    prompt=ChatPromptTemplate.from_template(
        """
        你是一个严谨的AI应用开发助手。
        
        请优先依据下面提供的参考资料回答问题。
        若资料没有包含答案，请明确说明资料不足，不要编造。
        回答时尽量简洁，并指出使用了哪些资料来源
        
        参考资料：{context}
        
        用户问题：{question}
        """
    )

    #7.检索和生成连接
    rag_chain=(
        {
            "context":retriever | RunnableLambda(format_docs),
            "question":RunnablePassthrough()
        }
        | prompt
        | model
        |StrOutputParser()
    )
    return rag_chain,retriever,chunks

def main():
    """观察切分与检索，再执行完整问答"""
    rag_chain,retriever,chunks=build_rag_chain()
    question="RAG是什么？是如何生成回答的"

    print("======文档切分结果======")
    print(f"chunk切分了{len(chunks)}")

    print("\n=========检索结果========")
    docs=retriever.invoke(question)

    for index,doc in enumerate(docs,start=1):
        print(f"\n第{index}个结果")
        print(f"来源{doc.metadata.get('source','unknown')}")
        print(doc.page_content)

    print("\n====RAG最终答案=====")
    answer=rag_chain.invoke(question)
    print(answer)

if __name__=="__main__":
        main()