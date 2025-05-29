import argparse
import asyncio
import logging

from src.config import config
from src.graph.graph import run_graph
from src.llms import LLMFactory
from src.sources import main as sources_main

logger = logging.Logger(__name__)


def arg_parser():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug logging"
    )
    return parser


def config_validate():
    if config.MODEL_PROVIDER not in LLMFactory.supported_llms:
        raise ValueError(f"Invalid model provider: {config.MODEL_PROVIDER}")


def setup_logging():
    # 配置根日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("app.log"),  # 输出到文件
            logging.StreamHandler(),  # 输出到控制台
        ],
    )


def main():
    """
    程序入口
    """
    config_validate()
    setup_logging()
    with open("./test.md", "r", encoding="utf-8") as f:
        content = f.read()
    asyncio.run(run_graph(content))


if __name__ == "__main__":
    main()
