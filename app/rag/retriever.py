
from dataclasses import dataclass

from app.rag.document_loader import Document

"""
简易内存向量检索器（召回模块）：
预先把文档切片和对应向量加载到内存；
用户查询-计算余弦相似度-排序（降序）-返回topK最相似的chunk
"""

@dataclass   #数据类，专门承载数据，自动生成__init__、__repr__,怒用手写构造函数
class SearchResult:
    """一次检索结果：文本块、相似度分数。"""
    document: Document
    score: float


# 余弦相似度函数
def cosine_similarity(
    vector_a: list[float],
    vector_b: list[float],
) -> float:
    """计算两个向量的余弦相似度。"""
    if len(vector_a) != len(vector_b):
        raise ValueError("两个向量的维度必须一致")

    if not vector_a:
        raise ValueError("向量不能为空")

#zip(vector_a, vector_b)---两个向量按位置配对（a1,b1）……
    dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
    norm_a = sum(a * a for a in vector_a) ** 0.5
    norm_b = sum(b * b for b in vector_b) ** 0.5

    if norm_a == 0 or norm_b == 0:
        raise ValueError("零向量无法计算余弦相似度")

    return dot_product / (norm_a * norm_b)

# 内存检索器（）持有知识点文档切片+向量 ，提供search召回接口
class VectorRetriever:
    """根据查询向量，从文本块中检索最相似的内容。"""

    def __init__(
        self,
        documents: list[Document],
        vectors: list[list[float]],
    ):
        if len(documents) != len(vectors):
            raise ValueError("文本块数量必须与向量数量一致")

        self.documents = documents
        self.vectors = vectors

        # 校验知识库内所有向量维度一致
        if vectors:
            dimension = len(vectors[0])
            if dimension == 0:
                raise ValueError("向量不能为空")

            for vector in vectors:
                if len(vector) != dimension:
                    raise ValueError("知识库向量的维度必须一致")

    # search检索方法
    def search(
        self,
        query_vector: list[float],
        top_k: int = 3,  #默认召回最相似chunk为3条
    ) -> list[SearchResult]:
        """返回相似度最高的前 top_k 个文本块。"""
        if top_k <= 0:
            raise ValueError("top_k 必须大于 0")

        if not self.documents:
            return []

        # 暴力检索
        scored_results = []

        for document, vector in zip(self.documents, self.vectors):
            score = cosine_similarity(query_vector, vector)
            scored_results.append(
                SearchResult(document=document, score=score)
            )

        # 原地排序
        scored_results.sort(
            key=lambda result: result.score,
            reverse=True, #降序
        )

        return scored_results[:top_k]
