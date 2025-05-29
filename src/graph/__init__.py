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

from .graph import get_tag_score_graph
from .nodes import (
    deduplicate_node,
    score_node,
    tagger_node,
)

__all__ = [
    "get_tag_score_graph",
    "tagger_node",
    "score_node",
    "deduplicate_node",
]
