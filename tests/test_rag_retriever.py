
import pytest

from app.rag.document_loader import Document
from app.rag.retriever import VectorRetriever, cosine_similarity


def test_cosine_similarity():
    score = cosine_similarity([1.0, 0.0], [1.0, 0.0])
    assert score == pytest.approx(1.0)


def test_retriever_returns_top_k_in_score_order():
    documents = [
        Document("天气晴朗", {"source": "weather.md"}),
        Document("RAG 是检索增强生成", {"source": "rag.md"}),
        Document("RAG 通过检索相关资料辅助回答", {"source": "rag.md"}),
    ]

    # 使用人工构造的向量测试排序，不调用真实模型
    vectors = [
        [0.0, 1.0],
        [1.0, 0.0],
        [0.8, 0.2],
    ]

    retriever = VectorRetriever(documents, vectors)
    results = retriever.search([1.0, 0.0], top_k=2)

    assert len(results) == 2
    assert results[0].document.content == "RAG 是检索增强生成"
    assert results[0].score >= results[1].score


def test_retriever_preserves_source_metadata():
    documents = [Document("RAG 介绍", {"source": "faq.md"})]
    retriever = VectorRetriever(documents, [[1.0, 0.0]])

    results = retriever.search([1.0, 0.0])

    assert results[0].document.metadata["source"] == "faq.md"


def test_retriever_rejects_mismatched_counts():
    with pytest.raises(ValueError):
        VectorRetriever(
            [Document("文本")],
            [],
        )


def test_cosine_similarity_rejects_zero_vector():
    with pytest.raises(ValueError):
        cosine_similarity([0.0, 0.0], [1.0, 0.0])
