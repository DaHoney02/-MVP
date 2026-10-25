from dataclasses import dataclass,field
from pathlib import Path


#dataclass：定义一个保存数据的类
@dataclass
class Document:
    """一份文档或一个文本片段"""
    content:str
    metadata:dict= field(default_factory=dict)

# Path:跨平台处理文件路径
# rglob("*"):递归搜索目录上的文件，包括子目录
# suffix:获取文件扩展名

def load_documents(directory:str | Path)-> list[Document]:
    """读取目录下所有TXT和MD文件"""
    root=Path(directory)

    if not root.exists():
        raise  FileNotFoundError(f"知识库目录不存在：{root}")

    if not root.is_dir():
        raise NotADirectoryError(f"路径不是目录：{root}")

    documents=[]
    #递归搜索，路径排序
    files=sorted(
        path for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".txt",".md"}
    )

    for path in files:
        content=path.read_text(encoding="utf-8").strip()

#         跳过空文件
        if not content:
            continue

        documents.append(
            Document(
                content=content,
                metadata={
                    # relative_to：计算path相对于root的相对路径
                    # as_posix：把Path对象转换为POSIX风格（/）路径字符串
                    "source":path.relative_to(root).as_posix()
                }
            )
        )
    return documents



