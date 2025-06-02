import os

from sqlalchemy import create_engine

from src.config import config

def get_db_url():
    sqlite_path = os.path.abspath(config.SQLITE_URL)
    return f"sqlite:///{sqlite_path}"

def get_db():
    """
    获取数据库引擎
    """
    # 创建数据库引擎
    db = create_engine(get_db_url(), echo=True, pool_size=10)
    return db


db = get_db()
