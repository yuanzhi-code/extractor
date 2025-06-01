import logging

from langchain_core.messages import HumanMessage  # 新增导入
from langgraph.types import Command
from sqlalchemy.orm import Session

from src.config import config
from src.graph._utils import get_response_property, pretty_response
from src.graph.state import State
from src.llms.factory import LLMFactory
from src.models import db
from src.models.score import EntryScore
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
          {state.entry_content}
          """
        )
    )
    response = llm.invoke(messages)
    pretty_response(response)
    logger.info(f"score node response: \n{response.pretty_repr()}")
    score = get_response_property(response, "tag")

    with Session(db) as session:
        _score = {
            "entry_id": state.entry_id,
            "score": score,
        }
        try:
            session.add(EntryScore(_score))
            session.commit()
        except Exception as e:
            session.rollback()
    if score == "noise":
        return Command(goto="__end__")
    return {"result": response}
