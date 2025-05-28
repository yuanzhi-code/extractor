import json
import logging

from langchain_core.messages import HumanMessage  # 新增导入
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
    messages.append(HumanMessage(
        content=f"""
        content which need to be scored:
          {state['content']}
          """
    ))
    response = llm.invoke(messages)
    response.content = response.content.strip()
    logger.info(f"score node response: \n{response.pretty_repr()}")
    if response.content.startswith("```json") and response.content.endswith("```"):
        response.content = response.content[len("```json") : -len("```")]
    with open("response-score.json", "w", encoding="utf-8") as f:
        f.write(response.content)
    return {"result": response}