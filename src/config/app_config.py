import dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

dotenv.load_dotenv(dotenv_path=".env", override=True)


class AppConfig(BaseSettings):
    NETWORK_PROXY: str = Field(
        description="代理地址，格式如 'http://127.0.0.1:7890'", default=""
    )
    SQLITE_URL: str = Field(
        description="SQLite URL", default="sqlite:///app.db"
    )
    LANGFUSE_SECRET_KEY: str = Field(
        description="Langfuse secret key", default=""
    )
    LANGFUSE_PUBLIC_KEY: str = Field(
        description="Langfuse public key", default=""
    )
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )
    folo_source: bool = Field(
        description="whether to enable read contents from folo sqlite",
        default=False,
    )
    # def __init__(self, proxy: Optional[str] = None):
    #     """
    #     初始化 FeedConfig

    #     Args:
    #         proxy: 可选的代理地址，格式如 'http://127.0.0.1:7890'
    #     """
    #     self.proxy = proxy
