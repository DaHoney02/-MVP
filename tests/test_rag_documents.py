
import pytest

from app.rag.document_loader import load_documents
from app.rag.text_splitter import split_documents


def test_load_markdown_document(tmp_path):
    """验证 Markdown 文件可以正确读取。"""

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    (docs_dir / "faq.md").write_text(
        "# 什么是 RAG？\nRAG 是检索增强生成。",
        encoding="utf-8",
    )

    documents = load_documents(docs_dir)

    assert len(documents) == 1
    assert "RAG 是检索增强生成" in documents[0].content
    assert documents[0].metadata["source"] == "faq.md"


def test_split_document_with_overlap():
    """验证文本切分、重叠和来源信息。"""

    from app.rag.document_loader import Document

    document = Document(
        content="ABCDEFGHIJKLMNO",
        metadata={"source": "faq.md"},
    )

    chunks = split_documents(
        [document],
        chunk_size=10,
        chunk_overlap=3,
    )

    assert [chunk.content for chunk in chunks] == [
        "ABCDEFGHIJ",
        "HIJKLMNO",
    ]

    assert chunks[0].metadata["source"] == "faq.md"
    assert chunks[1].metadata["chunk_index"] == 1


def test_split_rejects_invalid_overlap():
    """验证重叠长度不能大于或等于块长度。"""

    from app.rag.document_loader import Document

    document = Document(content="测试文本")

    with pytest.raises(ValueError):
        split_documents(
            [document],
            chunk_size=10,
            chunk_overlap=10,
        )


def test_load_rejects_missing_directory(tmp_path):
    """验证不存在的目录会给出明确错误。"""

    with pytest.raises(FileNotFoundError):
        load_documents(tmp_path / "missing")
