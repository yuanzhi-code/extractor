import logging
from typing import Literal

from langchain_core.messages import HumanMessage
from langgraph.types import Command, RunnableConfig
from sqlalchemy.orm import Session

from src.config import config as app_config
from src.graph._utils import get_response_property, pretty_response
from src.graph.state import ClassifyState
from src.graph.types import TagResult
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
            f"""content which need to be tagged:
            {state['entry'].get('content')}
            """
        )
    )
    response = llm.with_structured_output(TagResult).invoke(messages)
    # pretty_response(response)
    logger.info(f"tagger node response: \n{response}")

    # category = get_response_property(response, "name")
    # with Session(db) as session:
    #     try:
    #         _category = EntryCategory(
    #             {
    #                 "entry_id": state["entry"].get("id"),
    #                 "category": category,
    #             }
    #         )
    #         session.add(_category)
    #         session.commit()
    #     except Exception as e:
    #         session.rollback()
    # if category == "other":
    #     return Command(goto="__end__")
    return Command(
        update={"tag_result": response},
        goto="tagger_review",
    )


def tagger_review_node(state: ClassifyState) -> Command[Literal["score"]]:
    logger.info("tagger review node start")

    return Command(goto="score")
