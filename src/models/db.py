import os

from sqlalchemy import create_engine

from src.config.app_config import AppConfig


def get_db():
    """
    获取数据库引擎
    """
    app_config = AppConfig()
    sqlite_path = os.path.abspath(app_config.SQLITE_URL)
    # 设置数据库 URI
    DATABASE_URI = f"sqlite:///{sqlite_path}"
    # 创建数据库引擎
    db = create_engine(DATABASE_URI, echo=True, pool_size=10)
    return db


db = get_db()
