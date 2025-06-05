import logging

from langchain_core.messages import HumanMessage
from langgraph.types import Command
from sqlalchemy.orm import Session

from src.config import config as app_config
from src.graph._utils import extract_scorer_fields, upsert_record
from src.graph.state import ClassifyState
from src.llms import factory
from src.models import db
from src.models.entry_summary import EntrySummary
from src.models.score import EntryScore
from src.models.tags import EntryCategory
from src.prompts.prompts import get_prompt

logger = logging.getLogger(__name__)


def score_node(state: ClassifyState):
    """
    score the entry
    Args:
        state: ClassifyState
    Returns:
        dict: {"result": dict}
    """
    logger.info("score node start")
    category = state.get("category")

    # 如果state中没有category，从数据库查询
    if category is None:
        with Session(db) as session:
            entry_category = (
                session.query(EntryCategory)
                .filter(EntryCategory.entry_id == state["entry"].id)
                .first()
            )
            if entry_category:
                category = entry_category.category
                logger.info(f"Found existing category in database: {category}")
            else:
                raise ValueError("No category found in state or database")

    # 使用 HumanMessage 构造消息
    messages = get_prompt("scorer")
    model_provider = app_config.MODEL_PROVIDER
    llm = factory.get_llm(llm_type=model_provider)
    messages.append(
        HumanMessage(
            content=f"""
        请为以下内容进行评分和总结，以JSON格式返回：
        {{"tag": "评分结果", "summary": "内容总结"}}
        
        content which need to be scored:
          {state['entry'].content}
          """
        )
    )
    response = llm.invoke(messages)
    logger.info(f"score node response: \n{response.content}")

    # 使用工具函数处理response
    score, summary = extract_scorer_fields(response.content)

    with Session(db) as session:
        # 使用upsert处理EntryScore
        score_record, score_created = upsert_record(
            session=session,
            model_class=EntryScore,
            filter_kwargs={"entry_id": state["entry"].id},
            update_kwargs={"score": score},
        )
        logger.info(
            f"{'Created' if score_created else 'Updated'} score for entry {state['entry'].id}"
        )

        # 使用upsert处理EntrySummary
        summary_record, summary_created = upsert_record(
            session=session,
            model_class=EntrySummary,
            filter_kwargs={"entry_id": state["entry"].id},
            update_kwargs={"ai_summary": summary},
        )
        logger.info(
            f"{'Created' if summary_created else 'Updated'} summary for entry {state['entry'].id}"
        )

        session.commit()
    if score == "noise":
        return Command(goto="__end__")
    return {"result": {"tag": score, "summary": summary}}
