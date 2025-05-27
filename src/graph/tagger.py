import logging
from typing import Literal

from langchain_core.messages import AIMessage
from langgraph.types import Command

from llms.factory import LLMFactory
from prompts.prompts import get_prompt

logger = logging.getLogger(__name__)


def tagger_node() -> Command[Literal["score"]]:
    logger.info("tagger node")
    message = get_prompt("tagger")
    llm = LLMFactory.get_llm("ollama")
    response = llm.invoke(message)
    logger.info(f"tagger node response: {response}")

    # TODO(woxqaq): insert tags into database
    return Command(
        update={"message": AIMessage(content=response, name="tagger")}
    )
