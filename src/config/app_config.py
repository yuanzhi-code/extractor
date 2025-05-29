from typing import Optional

import dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

dotenv.load_dotenv(dotenv_path=".env", override=True)


class AppConfig(BaseSettings):
    NETWORK_PROXY: str = Field(
        description="代理地址，格式如 'http://127.0.0.1:7890'", default=""
    )
    OLLAMA_URL: str = Field(
        description="Ollama URL", default="http://localhost:11434"
    )
    OLLAMA_MODEL: str = Field(description="Ollama Model", default="qwen3:4b")
    SILICONFLOW_API_KEY: str = Field(
        description="SiliconFlow API Key", default=""
    )
    SILICONFLOW_MODEL: str = Field(
        description="SiliconFlow Model", default="Qwen/Qwen3-30B-A3B"
    )
    DEEPSEEK_API_KEY: str = Field(description="DeepSeek API Key", default="")
    DEEPSEEK_MODEL: str = Field(
        description="DeepSeek Model", default="deepseek-chat"
    )
    SQLITE_URL: str = Field(
        description="SQLite URL", default="sqlite:///app.db"
    )
    MODEL_PROVIDER: str = Field(description="Model Provider", default="ollama")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )
    # def __init__(self, proxy: Optional[str] = None):
    #     """
    #     初始化 FeedConfig

    #     Args:
    #         proxy: 可选的代理地址，格式如 'http://127.0.0.1:7890'
    #     """
    #     self.proxy = proxy
