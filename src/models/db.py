import os

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine

from src.config import config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def get_db_url():
    sqlite_path = os.path.abspath(config.SQLITE_URL)
    return f"sqlite:///{sqlite_path}"


# 连接事件处理函数 - 启用WAL模式
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """为SQLite数据库启用WAL模式"""
    if dbapi_connection:
        cursor = dbapi_connection.cursor()
        try:
            # 启用WAL模式
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")  # 推荐的同步模式
            cursor.execute("PRAGMA busy_timeout=5000;")  # 设置5秒超时

            # 获取当前日志模式
            cursor.execute("PRAGMA journal_mode;")
            result = cursor.fetchone()
            if result and isinstance(result, tuple):
                journal_mode = result[0]
                if journal_mode.lower() != "wal":
                    logger.warning(
                        f"⚠️ 警告: 无法启用WAL模式。当前模式为: {journal_mode}"
                    )
                else:
                    logger.info("✅ WAL模式已成功启用")
            else:
                logger.warning("⚠️ 警告: 无法获取当前日志模式")

        except Exception as e:
            logger.exception("❌ 启用WAL模式时出错:")
        finally:
            cursor.close()


def get_db():
    """
    获取数据库引擎
    """
    # 创建数据库引擎
    db = create_engine(
        get_db_url(),
        echo=True,
        pool_size=10,
        # 重要：关闭SQLite连接池的限制检查
        connect_args={"check_same_thread": False},
    )
    return db


db = get_db()
