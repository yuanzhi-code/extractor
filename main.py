import argparse
import asyncio
import logging
from pathlib import Path

import uvicorn

from src.graph.reporter_graph import run_reporter_graph
from src.llms.unified_manager import unified_llm_manager
from src.utils.logger import setup_logger
from src.workflows import run_classify_graph, run_crawl

# 使用一个全局变量来确保日志只配置一次
_logging_configured = False


def arg_parser():
    """
    parse the command line arguments
    """
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
    parser.add_argument(
        "--ignore-limit",
        action="store_true",
        help="ignore the limit of crawl",
    )
    parser.add_argument(
        "--limit", type=int, default=10, help="limit the number of crawl"
    )
    parser.add_argument(
        "--classify",
        action="store_true",
        help="Enable classify",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the server on (default: 8000)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to run the server on (default: 0.0.0.0)",
    )

    return parser.parse_args()


def configure_logging(debug: bool = False):
    """配置日志系统"""
    global _logging_configured

    if _logging_configured:
        return

    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # 设置日志级别
    level = logging.DEBUG if debug else logging.INFO
    setup_logger(level=level)

    # 获取根日志记录器并设置级别
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    _logging_configured = True


def initialize_llm():
    """初始化LLM系统"""
    logger = logging.getLogger(__name__)
    logger.info("初始化统一LLM系统...")

    # 初始化统一LLM管理器
    unified_llm_manager.initialize()

    # 获取配置信息
    config_info = unified_llm_manager.get_config_info()
    logger.info(f"LLM系统配置: {config_info}")


def main():
    args = arg_parser()

    # 配置日志
    configure_logging(args.debug)
    logger = logging.getLogger(__name__)

    # 初始化LLM系统
    try:
        initialize_llm()
    except Exception as e:
        logger.exception("LLM系统初始化失败")
        return

    if args.graph:
        logger.info("Starting graph test...")
        asyncio.run(run_reporter_graph())
    elif args.crawl:
        logger.info("Starting crawl...")
        run_crawl(
            enable_limit=not args.ignore_limit,
            limit=args.limit,
        )
    elif args.classify:
        logger.info("Starting classify...")
        asyncio.run(run_classify_graph())
    else:
        logger.info("Starting API server...")
        from src import app

        uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
