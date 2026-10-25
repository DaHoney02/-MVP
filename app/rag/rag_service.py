from dataclasses import dataclass
from pathlib import Path

from app.llm_client import LLMClient
from app.rag.document_loader import load_documents
from app.rag.embedding_client import EmbeddingClient
from app.rag.retriever import VectorRetriever, SearchResult
from app.rag.text_splitter import split_documents
from app.schemas.schemas import Message


@dataclass
class RAGAnswer:
    """RAG回答及其引用来源"""
    answer:str
    sources:list[dict]

class RAGService:
    """整合文档、Embedding、检索+LLM的RAG服务"""
    def __init__(
        self,
        embedding_client=None,
        llm_client=None,
        docs_path:str|Path="knowledge_base/docs",  #python文件路径工具，支持字符串/path混用，跨平台路径处理
        top_k:int=3
    ):
        self.embedding_client=embedding_client or EmbeddingClient()
        self.llm_client=llm_client or LLMClient()
        self.top_k=top_k

        # 读取目录所有文档，返回文档对象列表，每个文档包含content+metadata
        documents=load_documents(docs_path)
        if not documents:
            raise ValueError("知识库没有读取的文档")

        self.chunks=split_documents(documents)
        if not self.chunks:
            raise ValueError("知识库没有生成有效的chunk")

        # 批量向量化
        vectors=self.embedding_client.embed_texts(
            [chunk.content for chunk in self.chunks]
        )
        if len(vectors) !=len(self.chunks):
            raise ValueError("文本数量与生成的向量数量不一致")

        # 将chunks+对应向量传入检索器
        self.retriever=VectorRetriever(self.chunks,vectors)


    def ask(self,question:str,top_k:int | None=None)->RAGAnswer:
        """检索相关知识，让LLM根据资料回答"""
        question=question.strip()  #防御性校验
        if not question:
            raise ValueError("问题不能为空")

        query_vector=self.embedding_client.embed_texts([question])[0]
        results:list[SearchResult]=self.retriever.search(
            query_vector,
            top_k=top_k if top_k is not None else self.top_k,
        )

        if not results:
            raise ValueError("知识库没有可用于检索的文本")

        content_parts=[]
        for index,result in enumerate(results,start=1):
            source=result.document.metadata.get("source","未知来源")
            content_parts.append(
                f"[资源{index}|来源：{source}]\n"
                f"{result.document.content}"
            )
        context="\n\n".join(content_parts)

        messages=[
            Message(
                role="system",
                content=(
                    "你是一个严谨的知识库问答助手。"
                    "请优先依据用户提供的参考资料回答。"
                    "如果资料不足以回答问题，请明确说明资料不足，"
                    "不要编造事实。"
                    "回答中应指出所依据的资料编号，例如[资料 1]。"
                ),
            ),
            Message(
                role="user",
                content=(
                    f"参考资料：\n{context}\n\n"
                    f"用户问题：{question}"
                ),
            )
        ]

        answer=self.llm_client.chat(messages)

        sources=[
            {
                "source":result.document.metadata.get("source","未知来源"),
                "chunk_index":result.document.metadata.get("chunk_index"),
                "score":result.score,
                "content":result.document.content
            }
            for result in results
        ]

        return RAGAnswer(answer=answer,sources=sources)


