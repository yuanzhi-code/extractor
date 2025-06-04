import logging
import sys
from typing import Optional

import colorlog


def setup_logger(name: Optional[str] = None) -> logging.Logger:
    """
    设置带有颜色的日志记录器

    Args:
        name: 日志记录器名称，如果为None则返回根日志记录器

    Returns:
        logging.Logger: 配置好的日志记录器
    """
    logger = logging.getLogger(name)

    # 如果已经有处理器，说明已经配置过，直接返回
    if logger.handlers:
        return logger

    # 创建控制台处理器
    handler = colorlog.StreamHandler(sys.stdout)

    # 设置日志格式和颜色
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    return logger
