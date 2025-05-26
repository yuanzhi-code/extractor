import logging
import os

from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.declarative import declarative_base

sqlite_path = os.path.abspath("app.db")

# 设置数据库 URI
DATABASE_URI = f"sqlite:///{sqlite_path}"

# 创建数据库引擎
db = create_engine(DATABASE_URI, echo=True, pool_size=10)
