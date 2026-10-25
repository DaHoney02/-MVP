from types import SimpleNamespace

import pytest

from app.rag.embedding_client import EmbeddingClient



class FakeEmbeddings:
    def __init__(self):
        self.calls = []

    def create(self, model, input, encoding_format):
        self.calls.append({
            "model": model,
            "input": input,
            "encoding_format": encoding_format,
        })

        data = [
            SimpleNamespace(
                index=i,
                embedding=[float(i), 0.5],
            )
            for i in range(len(input))
        ]

        # 模拟 API 返回乱序数据，验证客户端能否恢复顺序
        return SimpleNamespace(data=list(reversed(data)))


class FakeClient:
    def __init__(self):
        self.embeddings=FakeEmbeddings()

def text_embed_texts_return_input_order():
    fake_client=FakeClient()
    embedding_client=EmbeddingClient(client=fake_client)

    vectors=embedding_client.embed_texts(["文本1","文本2"])

    assert vectors==[[0.0,0.5],[1.0,0.5]]
    assert fake_client.embeddings.calls[0]["input"]==["文本1","文本2"]

def test_embed_texts_batches_at_most_ten_items():
    fake_client=FakeClient()
    embedding_client=EmbeddingClient(client=fake_client)

    vectors=embedding_client.embed_texts([f"文本{i}" for i in range(12)])

    assert len(vectors)==12
    assert len(fake_client.embeddings.calls)==2
    assert len(fake_client.embeddings.calls[0]["input"])==10
    assert len(fake_client.embeddings.calls[1]["input"])==2

def test_embed_texts_returns_empty_list_for_empty_input():
    fake_client = FakeClient()
    embedding_client = EmbeddingClient(client=fake_client)

    assert embedding_client.embed_texts([]) == []
    assert fake_client.embeddings.calls == []


def test_embed_texts_rejects_blank_text():
    embedding_client = EmbeddingClient(client=FakeClient())

    with pytest.raises(ValueError):
        embedding_client.embed_texts(["正常文本", "   "])