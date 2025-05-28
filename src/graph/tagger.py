import json
import logging
from typing import Literal

from langchain_core.messages import AIMessage
from langgraph.types import Command

from src.config import config
from src.graph.state import State
from src.llms.factory import LLMFactory
from src.prompts.prompts import get_prompt

logger = logging.getLogger(__name__)


def tagger_node(state: State) -> Command[Literal["score"]]:
    logger.info("tagger node")
    model_provider = config.MODEL_PROVIDER
    llm = LLMFactory().get_llm(model_provider)
    message = get_prompt("tagger", model_name=llm.model_name)
    message += [
        {
            "role": "user",
            "content": f"""content which need to be tagged:
          {state['messages'][-1].content}
          """,
        }
    ]
    response = llm.invoke(message)
    response.content = response.content.strip()
    # for some models, the response is wrapped in ```json, so we need to remove it
    if response.content.startswith("```json") and response.content.endswith(
        "```"
    ):
        response.content = response.content[len("```json") : -len("```")]
    with open("response-tagger.json", "w", encoding="utf-8") as f:
        f.write(response.content)

    # TODO(woxqaq): insert tags into database
    full_resp = response.content
    response_json = json.loads(full_resp)
    logger.info(f"tagger node response_json: {response_json}")
    return Command(
        update={
            "category": response_json["name"],
        },
        goto="score",
    )
