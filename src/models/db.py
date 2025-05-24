from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.declarative import declarative_base

# 设置数据库 URI
DATABASE_URI = 'sqlite:///extractor.db'

# 创建数据库引擎
engine = create_engine(DATABASE_URI, echo=True, pool_size=10)

# 声明基类
Base = declarative_base()

# TODO add orm models definitions here

# 创建所有表
Base.metadata.create_all(engine)
