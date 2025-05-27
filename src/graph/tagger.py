import logging
from typing import Literal

from langchain_core.messages import AIMessage
from langgraph.types import Command

from src.graph.state import State
from src.llms.factory import LLMFactory
from src.prompts.prompts import get_prompt

logger = logging.getLogger(__name__)


def tagger_node(state: State) :
    logger.info("tagger node")
    message = get_prompt("tagger")
    llm = LLMFactory().get_llm("ollama")
    message += [
        {
            "role": "user",
            "content": f"""content which need to be tagged:
          {state['messages'][-1].content}
          """,
        }
    ]
    response = llm.invoke(message)
    print(response)
    logger.info(f"tagger node response: {response}")

    # TODO(woxqaq): insert tags into database
    return {
        "result": response
    }
