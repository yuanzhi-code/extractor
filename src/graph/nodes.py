import json
import logging
from typing import Literal

from langchain_core.messages import BaseMessage, HumanMessage  # 新增导入
from langgraph.types import Command

from src.config import config
from src.graph.state import State
from src.llms.factory import LLMFactory
from src.prompts.prompts import get_prompt

logger = logging.getLogger(__name__)


def _get_llm():
    return LLMFactory().get_llm(config.MODEL_PROVIDER)


def _format_response(response: BaseMessage):
    response.content = response.content.strip()
    # for some models, the response is wrapped in ```json, so we need to remove it
    if response.content.startswith("```json") and response.content.endswith(
        "```"
    ):
        response.content = response.content[len("```json") : -len("```")]
    return response


def tagger_node(state: State) -> Command[Literal["score"]]:
    logger.info("tagger node start")
    messages = get_prompt("tagger")
    llm = _get_llm()
    messages.append(HumanMessage(f"{state['content']}"))
    response = llm.invoke(messages)
    response = _format_response(response)
    logger.info(f"tagger node response: \n{response.pretty_repr()}")

    # TODO(woxqaq): insert tags into database
    # return {"result": response, "next": "score"}
    response_json = json.loads(response.content)
    category = response_json["name"]
    if category == "other":
        return Command(goto="__end__")
    return Command(
        update={"category": category},
        goto="score",
    )


def score_node(state: State):
    logger.info("score node start")
    prev_category = state.get("category")
    if prev_category is None:
        raise ValueError("No category found")

    if prev_category not in ["tech", "business", "experience"]:
        raise ValueError("Invalid category")

    # 修改: 使用 HumanMessage 构造消息
    messages = get_prompt("scorer")
    llm = _get_llm()
    messages.append(HumanMessage(f"{state['content']}"))
    response = llm.invoke(messages)
    response = _format_response(response)
    logger.info(f"score node response: \n{response.pretty_repr()}")
    return {"result": response}


def deduplicate_node(state: State):
    logger.info("deduplicate node start")
    messages = get_prompt("deduplicator")
    llm = _get_llm()
    messages.append(HumanMessage(f"{state['content']}"))
