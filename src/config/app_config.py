
# file: /Users/woxqaq/extractor/src/config/feed_config.py

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    NETWORK_PROXY: str = Field(
        description="代理地址，格式如 'http://127.0.0.1:7890'"
        ,default=""
    )
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
        ,extra="ignore"
    )
    # def __init__(self, proxy: Optional[str] = None):
    #     """
    #     初始化 FeedConfig

    #     Args:
    #         proxy: 可选的代理地址，格式如 'http://127.0.0.1:7890'
    #     """
    #     self.proxy = proxy