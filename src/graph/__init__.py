"""
graph package
"""

import logging

# 创建graph包的日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 创建文件处理器，将日志写入graph.log
file_handler = logging.FileHandler("graph.log")
file_handler.setLevel(logging.INFO)

# 设置日志格式
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(formatter)

# 添加处理器到logger
logger.addHandler(file_handler)

from .graph import (
    get_classification_graph,
    get_reporter_graph,
    run_graph,
    run_reporter_graph,
)

__all__ = [
    "get_classification_graph",
    "get_reporter_graph",
    "run_graph",
    "run_reporter_graph",
]
