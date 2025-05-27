import os

from sqlalchemy import create_engine

from src.config import config


def get_db():
    """
    获取数据库引擎
    """
    sqlite_path = os.path.abspath(config.SQLITE_URL)
    # 设置数据库 URI
    DATABASE_URI = f"sqlite:///{sqlite_path}"
    # 创建数据库引擎
    db = create_engine(DATABASE_URI, echo=True, pool_size=10)
    return db


db = get_db()
