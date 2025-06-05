import logging
from typing import Literal

from langchain_core.messages import HumanMessage
from langgraph.types import Command, RunnableConfig
from sqlalchemy.orm import Session

from src.config import config as app_config
from src.graph._utils import (
    extract_category_from_review,
    parse_llm_json_response,
    upsert_record,
)
from src.graph.state import ClassifyState
from src.llms import factory
from src.models import db
from src.models.tags import EntryCategory
from src.prompts.prompts import get_prompt

logger = logging.getLogger(__name__)


def tagger_node(state: ClassifyState, config: RunnableConfig) -> Command:
    logger.info("tagger node start")
    with Session(db) as session:
        entry_category = (
            session.query(EntryCategory)
            .filter(EntryCategory.entry_id == state["entry"].id)
            .first()
        )
        # 已存在分类，直接跳过
        if entry_category:
            logger.info(f"entry {state['entry'].id} has been tagged")
            logger.info(f"Existing category: {entry_category.category}")
            return Command(
                update={"category": entry_category.category}, goto="score"
            )

    messages = get_prompt("tagger")
    model_provider = app_config.MODEL_PROVIDER
    llm = factory.get_llm(llm_type=model_provider)
    messages.append(
        HumanMessage(
            f"""
            现在请对原始内容进行分类，并给出你的分类结果，以JSON格式返回：
            {{"name": "分类名称", "classification_rationale": "分类理由"}}
            
            原始内容:{state['entry'].content}
            """
        )
    )
    response = llm.invoke(messages)
    logger.info(f"tagger node response: \n{response.content}")

    # 解析响应
    tag_result_data = parse_llm_json_response(response.content)

    return Command(
        update={"tag_result": tag_result_data},
        goto="tagger_review",
    )


def tagger_review_node(state: ClassifyState) -> Command[Literal["score"]]:
    logger.info("tagger review node start")
    messages = get_prompt("tagger_review")
    model_provider = app_config.MODEL_PROVIDER
    llm = factory.get_llm(llm_type=model_provider)
    tag_result = state["tag_result"]
    messages.append(
        HumanMessage(
            f"""
            现在请你对分类结果进行审查，并给出你的评审意见和修改结果，以JSON格式返回：
            {{"approved": true/false, "reason": "审查理由", "comment": {{"name": "新分类名称", "classification_rationale": "新分类理由"}} }}
            
            如果approved为true，则comment可以为null。如果approved为false，请在comment中提供新的分类建议。
            
            分类结果:{tag_result}
            原始内容:{state['entry'].content}
            """
        )
    )
    response = llm.invoke(messages)
    logger.info(f"tagger review node response: \n{response.content}")

    # 解析响应并提取category
    response_data = parse_llm_json_response(response.content)
    category = extract_category_from_review(response_data, tag_result)

    with Session(db) as session:
        try:
            logger.info(
                f"About to save category: {category} for entry {state['entry'].id}"
            )

            # 使用upsert处理EntryCategory
            category_record, category_created = upsert_record(
                session=session,
                model_class=EntryCategory,
                filter_kwargs={"entry_id": state["entry"].id},
                update_kwargs={"category": category},
            )
            logger.info(
                f"{'Created' if category_created else 'Updated'} category for entry {state['entry'].id}"
            )

            session.commit()
            logger.info("Successfully saved category")
        except Exception as e:
            logger.exception("tagger node error:")
            session.rollback()
    if category == "other":
        return Command(goto="__end__")
    logger.info("Returning command with category")
    return Command(
        update={"category": category},
        goto="score",
    )
