
from app.rag.rag_service import RAGService


class FakeEmbeddingClient:
    def embed_texts(self, texts):
        vectors = []

        for text in texts:
            if "天气" in text:
                vectors.append([0.0, 1.0])
            else:
                vectors.append([1.0, 0.0])

        return vectors


class FakeLLMClient:
    def __init__(self):
        self.messages = None

    def chat(self, messages):
        self.messages = messages
        return "根据参考资料，RAG 是检索增强生成。[资料 1]"


def test_rag_service_answers_with_retrieved_context(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    (docs_dir / "rag.md").write_text(
        "RAG 是检索增强生成技术。",
        encoding="utf-8",
    )
    (docs_dir / "weather.txt").write_text(
        "天气晴朗，适合户外活动。",
        encoding="utf-8",
    )

    fake_llm = FakeLLMClient()
    service = RAGService(
        embedding_client=FakeEmbeddingClient(),
        llm_client=fake_llm,
        docs_path=docs_dir,
        top_k=1,
    )

    result = service.ask("什么是 RAG？")

    assert "RAG" in result.answer
    assert len(result.sources) == 1
    assert result.sources[0]["source"] == "rag.md"
    assert result.sources[0]["score"] > 0
    assert fake_llm.messages is not None


def test_rag_service_rejects_blank_question(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "faq.md").write_text(
        "RAG 是检索增强生成。",
        encoding="utf-8",
    )

    service = RAGService(
        embedding_client=FakeEmbeddingClient(),
        llm_client=FakeLLMClient(),
        docs_path=docs_dir,
    )

    import pytest

    with pytest.raises(ValueError, match="问题不能为空"):
        service.ask("   ")
