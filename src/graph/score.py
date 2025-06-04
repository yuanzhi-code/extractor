import logging

from langchain_core.messages import HumanMessage  # 新增导入
from langgraph.types import Command
from sqlalchemy.orm import Session

from src.config import config
from src.graph.state import ClassifyState
from src.graph.types import ScorerOutput
from src.llms.factory import LLMFactory
from src.models import db
from src.models.entry_summary import EntrySummary
from src.models.score import EntryScore
from src.prompts.prompts import get_prompt

logger = logging.getLogger(__name__)


def score_node(state: ClassifyState):
    logger.info("score node start")
    tag_result = state.get("tag_result")
    if tag_result is None:
        raise ValueError("No tag result found")

    # 修改: 使用 HumanMessage 构造消息
    messages = get_prompt("scorer")
    model_provider = config.MODEL_PROVIDER
    llm = LLMFactory().get_llm(model_provider)
    messages.append(
        HumanMessage(
            content=f"""
        content which need to be scored:
          {state['entry'].content}
          """
        )
    )
    response = llm.with_structured_output(ScorerOutput).invoke(messages)
    logger.info(f"score node response: \n{response}")
    score = response.tag
    summary = response.summary

    with Session(db) as session:
        _score = {
            "entry_id": state["entry"].id,
            "score": score,
        }
        session.add(EntryScore(_score))
        session.add(
            EntrySummary(entry_id=state["entry"].id, summary=summary)
        )
    if score == "noise":
        return Command(goto="__end__")
    return {"result": response}
