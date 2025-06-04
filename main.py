import argparse
import asyncio
import logging
from pathlib import Path

import uvicorn

from src.config import config
from src.graph.reporter_graph import run_reporter_graph
from src.llms import LLMFactory
from src.utils.logger import setup_logger
from src.workflows import run_crawl, run_graph

logger = setup_logger(__name__)


def arg_parser():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug logging"
    )
    parser.add_argument(
        "--graph",
        action="store_true",
        help="Enable test graph",
    )
    parser.add_argument(
        "--crawl",
        action="store_true",
        help="Enable crawl",
    )
    return parser


def config_validate():
    if config.MODEL_PROVIDER not in LLMFactory.supported_llms:
        raise ValueError(f"Invalid model provider: {config.MODEL_PROVIDER}")


def setup_logging():
    """
    设置日志系统
    - 使用彩色日志输出到控制台
    - 同时保存到文件
    """
    # 获取根日志记录器
    root_logger = setup_logger()

    # 添加文件处理器
    file_handler = logging.FileHandler("app.log")
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # 设置日志级别
    root_logger.setLevel(logging.INFO)


def main():
    """
    程序入口
    """
    config_validate()
    setup_logging()
    contents = []
    for md_file in Path("testdata").glob("*.md"):
        with open(md_file, encoding="utf-8") as f:
            contents.append(f.read())
    run_reporter_graph(contents)


if __name__ == "__main__":
    setup_logging()
    args = arg_parser().parse_args()
    if args.graph:
        asyncio.run(run_graph(False))
    elif args.crawl:
        asyncio.run(run_crawl())
    else:
        uvicorn.run("src.app:app", reload=False, log_level="info")
