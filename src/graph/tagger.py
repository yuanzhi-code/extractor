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
from src.models.tags import EntriesCategories
from src.prompts.prompts import get_prompt

logger = logging.getLogger(__name__)


def tagger_node(state: State) -> Command[Literal["score"]]:
    logger.info("tagger node start")
    messages = get_prompt("tagger")
    model_provider = config.MODEL_PROVIDER
    llm = LLMFactory().get_llm(model_provider)
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

    category = get_response_property(response, "name")
    with Session(db) as session:
        try:
            _category = EntriesCategories(
                {
                    "entry_id": state["entry"].get("id"),
                    "category": category,
                }
            )
            session.add(_category)
            session.commit()
        except Exception as e:
            session.rollback()
    if category == "other":
        return Command(goto="__end__")
    return Command(
        update={"category": category},
        goto="score",
    )
