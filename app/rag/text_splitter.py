from app.rag.document_loader import Document


def split_documents(
        documents:list[Document],
        chunk_size:int=200,
        chunk_overlap:int=30,  #重叠部分
)->list[Document]:
    """按字符数切分文档，并保留来源信息"""

    if chunk_size<=0:
        raise ValueError("chunk_size 必须大于0")

    if chunk_overlap<0 or chunk_overlap>=chunk_size:
        raise  ValueError("chunk_overlap必须大于等于0，且小于chunk_size")

    chunks=[]
    step=chunk_size-chunk_overlap

    for document in documents:
        text=document.content.strip()

        if not text:
            continue

        chunk_index=0
        for start in range(0,len(text),step):
            content=text[start:start+chunk_size]

            if not content:
                break

            metadata={
                **document.metadata,
                "chunk_index":chunk_index
            }

            chunks.append(
                Document(content=content,metadata=metadata)
            )

            chunk_index +=1

            if start+chunk_size>=len(text):
                break
    return chunks