import logging
from typing import Literal

from langchain_core.messages import HumanMessage
from langgraph.types import Command
from sqlalchemy.orm import Session

from src.config import config
from src.graph._utils import get_response_property, pretty_response
from src.graph.state import State
from src.llms.factory import LLMFactory
from src.models import db
from src.models.tags import EntryCategory
from src.prompts.prompts import get_prompt

logger = logging.getLogger(__name__)


def tagger_node(state: State) -> Command[Literal["score"]]:
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
    model_provider = config.MODEL_PROVIDER
    llm = LLMFactory().get_llm(model_provider, model=None)
    messages.append(
        HumanMessage(
            f"""content which need to be tagged:
            {state['entry'].get('content')}
            """
        )
    )
    response = llm.invoke(messages)
    pretty_response(response)
    logger.info(f"tagger node response: \n{response.pretty_repr()}")

    try:
        category = get_response_property(response, "name")
        logger.info(f"Extracted category: {category}")
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
        update={"category": category},
        goto="score",
    )
