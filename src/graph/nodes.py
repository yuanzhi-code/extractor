import json
import logging
from typing import Literal

from langchain_core.messages import HumanMessage  # 新增导入
from langgraph.types import Command

from src.config import config
from src.graph.state import State
from src.llms.factory import LLMFactory
from src.prompts.prompts import get_prompt

logger = logging.getLogger(__name__)


def score_node(state: State):
    logger.info("score node start")
    prev_category = state.get("category")
    if prev_category is None:
        raise ValueError("No category found")

    if prev_category not in ["tech", "business", "experience"]:
        raise ValueError("Invalid category")

    # 修改: 使用 HumanMessage 构造消息
    messages = get_prompt("scorer")
    model_provider = config.MODEL_PROVIDER
    llm = LLMFactory().get_llm(model_provider)
    messages.append(
        HumanMessage(
            content=f"""
        content which need to be scored:
          {state['content']}
          """
        )
    )
    response = llm.invoke(messages)
    response.content = response.content.strip()
    logger.info(f"score node response: \n{response.pretty_repr()}")
    if response.content.startswith("```json") and response.content.endswith(
        "```"
    ):
        response.content = response.content[len("```json") : -len("```")]
    return {"result": response}

def tagger_node(state: State) -> Command[Literal["score"]]:
    logger.info("tagger node start")
    messages = get_prompt("tagger")
    model_provider = config.MODEL_PROVIDER
    llm = LLMFactory().get_llm(model_provider)
    messages.append(
        HumanMessage(
            f"""content which need to be tagged:
            {state['content']}
            """
        )
    )
    response = llm.invoke(messages)
    response.content = response.content.strip()
    # for some models, the response is wrapped in ```json, so we need to remove it
    if response.content.startswith("```json") and response.content.endswith(
        "```"
    ):
        response.content = response.content[len("```json") : -len("```")]
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

def deduplicate_node(state: State):
    logger.info("deduplicate node start")
    embedding_model = LLMFactory().get_embedding_model(config.MODEL_PROVIDER)
    embedding = embedding_model.embed_query(state["content"])
    
    return {"result": embedding}