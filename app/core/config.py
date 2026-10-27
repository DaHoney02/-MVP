
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置:统一读取.env和系统环境变量"""
    # 应用配置
    DEBUG:bool=True

    # 大模型配置
    DASHSCOPE_API_KEY:str
    DASHSCOPE_BASE_URL:str ="https://dashscope.aliyuncs.com/compatible-mode/v1"
    MODEL_NAME:str="qwen3.8-flash"
    EMBEDDING_MODEL:str="qwen3.7-text-embedding-flash"

    # PostgreSQL配置
    POSTGRES_USER: str = "aftercare_app"
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = "little_aftercare"

    # 运行时，通过映射端口5433连接容器
    POSTGRES_HOST: str = "127.0.0.1"
    POSTGRES_PORT: int = 5433

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra='ignore'
    )

# 创建全局配置对象
# 实例化会读取环境变量，并校验必填配置
settings = Settings()
