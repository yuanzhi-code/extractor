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
from src.models.rss_entry import RssEntry
from src.models.tags import EntryCategory
from src.prompts.prompts import get_prompt

logger = logging.getLogger(__name__)


def tagger_node(state: ClassifyState, config: RunnableConfig) -> Command:
    logger.info("tagger node start")
    messages = get_prompt("tagger")
    model_provider = app_config.MODEL_PROVIDER
    llm = factory.get_llm(llm_type=model_provider)
    messages.append(
        HumanMessage(
            f"""
            现在请对原始内容进行分类，并给出你的分类结果
            原始内容:{state['entry'].get('content')}
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
            原始内容:{state['entry'].get('content')}
            """
        )
    )
    response = llm.with_structured_output(TaggerReviewResult).invoke(messages)
    logger.info(f"tagger review node response: \n{response}")

    if not isinstance(response, TaggerReviewResult):
        raise ValueError("response is not a [TaggerReviewResult]")

    with Session(db) as session:
        if not response.approved:
            tag_result = TagResult(**response.comment)
        session.add(tag_result.to_entry_category(state["entry"].get("id")))

    return Command(
        update={"tag_result": tag_result},
        goto="score",
    )
