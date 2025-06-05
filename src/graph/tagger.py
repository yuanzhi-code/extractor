import logging
from typing import Literal

from langchain_core.messages import HumanMessage
from langgraph.types import Command, RunnableConfig
from numpy import isin
from sqlalchemy.orm import Session

from src.config import config as app_config
from src.graph._utils import get_response_property, pretty_response
from src.graph.state import ClassifyState
from src.graph.types import TaggerReviewResult, TagResult
from src.llms import factory
from src.llms.factory import LLMFactory
from src.models import db
from src.models.tags import EntryCategory
from src.prompts.prompts import get_prompt

logger = logging.getLogger(__name__)


def tagger_node(state: ClassifyState, config: RunnableConfig) -> Command:
    logger.info("tagger node start")
    with Session(db) as session:
        entry_category = (
            session.query(EntryCategory)
            .filter(EntryCategory.entry_id == state["entry"].get("id"))
            .first()
        )
        # 已存在分类，直接跳过
        if entry_category:
            logger.info(f"entry {state['entry'].get('id')} has been tagged")
            logger.info(f"Existing category: {entry_category.category}")
            return Command(
                update={"category": entry_category.category},
                goto="score"
            )

    messages = get_prompt("tagger")
    model_provider = app_config.MODEL_PROVIDER
    llm = factory.get_llm(llm_type=model_provider)
    messages.append(
        HumanMessage(
            f"""
            现在请对原始内容进行分类，并给出你的分类结果
            原始内容:{state['entry'].content}
            """
        )
    )
    response = llm.with_structured_output(TagResult).invoke(messages)
    # pretty_response(response)
    logger.info(f"tagger node response: \n{response}")

    return Command(
        update={"tag_result": response},
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
            现在请你对分类结果进行审查，并给出你的评审意见和修改结果
            分类结果:{tag_result}
            原始内容:{state['entry'].content}
            """
        )
    )
    response = llm.with_structured_output(TaggerReviewResult).invoke(messages)
    logger.info(f"tagger review node response: \n{response}")

    try:
        if not isinstance(response, TaggerReviewResult):
            logger.info(f"Extracted category: {response}")
            raise ValueError("response is not a [TaggerReviewResult]")
    except Exception as e:
        logger.exception("Failed to extract category from response:")
        logger.exception(f"Response content: {response.content}")
        # If we can't extract category, mark as 'other' to prevent total failure
        category = "other"


    with Session(db) as session:
        try:
            logger.info(f"About to save category: {category} for entry {state['entry'].get('id')}")
            _category = EntryCategory(
                **{
                    "entry_id": state["entry"].get("id"),
                    "category": category,
                }
            )
            session.add(_category)
            session.commit()
            logger.info("Successfully saved category")
        except Exception as e:
            logger.exception("tagger node error:")
            session.rollback()
    if category == "other":
        return Command(goto="__end__")
    logger.info("Returning command with category")
    return Command(
        update={"tag_result": tag_result},
        goto="score",
    )
