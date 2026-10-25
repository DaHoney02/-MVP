from openai import OpenAI

from app.core.config import settings

"""调用向量模型，文本转换成数字列表"""

class EmbeddingClient:
    """使用openai官方SDK访问：负责调用embedding模型，将文本转为向量"""
    def __init__(self,client=None):
        self.client=client or OpenAI(
            api_key=settings.DASHSCOPE_API_KEY,
            base_url=settings.DASHSCOPE_BASE_URL,
            timeout=30.0,
            max_retries=2  #网络抖动自动重试2次
        )
        self.model=settings.EMBEDDING_MODEL

    def embed_texts(self,texts:list[str])->list[list[float]]:
        """将多段文本转成向量，保持输入顺序"""
        if not texts:
            return []

        # any（itemable）:只要迭代器任意一值为True,整体返回True，全部False才返回False
        if any(not text.strip() for text in texts):
            raise ValueError("待向量化的文本不能为空")

        vector=[]

        for start in range(0,len(texts),10):
            batch=texts[start:start+10]  #切片

            response=self.client.embeddings.create(
                model=self.model,
                input=batch,  #支持传入字符串列表，批量编码
                encoding_format="float"  #指定返回浮点数数组
            )

            # 关键：根据index排序，去报向量顺序与文本顺序一致（openai接口返回不保证顺序与传入的顺序一致）
            items=sorted(response.data,key=lambda item:item.index)
            vector.extend(item.embedding for item in items)     #extend追加列表

        return vector
