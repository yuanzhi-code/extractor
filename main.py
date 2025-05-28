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


def main():
    """
    程序入口
    """
    config_validate()
    
    args = arg_parser().parse_args()
    logLevel = logging.INFO
    if args.debug:
        logLevel = logging.DEBUG
    logging.basicConfig(
        level=logLevel,
        format="%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s",
    )
    with open("./test.md", "r", encoding="utf-8") as f:
        content = f.read()
    asyncio.run(run_graph(content))


if __name__ == "__main__":
    main()
