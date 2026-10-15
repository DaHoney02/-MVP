
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""
    DEBUG:bool=True
    DASHSCOPE_API_KEY:str
    DASHSCOPE_BASE_URL:str = "https: // dashscope.aliyuncs.com / compatible - mode / v1"
    MODEL_NAME:str="qwen3.8-flash"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra='ignore'
    )

settings=Settings()
