import logging

from langchain_core.messages import HumanMessage
from langgraph.types import Command, RunnableConfig
from sqlalchemy.orm import Session

from src.graph._utils import (
    parse_llm_json_response,
    upsert_record,
)
from src.graph.state import ClassifyState
from src.llms.unified_manager import unified_llm_manager
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
    # 使用统一LLM管理器，为tagger节点获取专用模型
    llm = unified_llm_manager.get_llm(node_name="tagger")
    messages.append(
        HumanMessage(
            f"""
            现在请对原始内容进行分类，并给出你的分类结果
            
            原始内容:{state['entry'].content}
            """
        )
    )

    try:
        response = llm.invoke(messages)
        logger.info(f"tagger node response: \n{response.content}")

        # 解析响应
        tag_result_data = parse_llm_json_response(response.content)
    except Exception:
        logger.exception("LLM调用失败，分类任务无法完成")
        # 返回到结束状态，避免无限重试
        return Command(goto="__end__")

    with Session(db) as session:
        upsert_record(
            session=session,
            model_class=EntryCategory,
            filter_kwargs={"entry_id": state["entry"].id},
            update_kwargs={
                "category": tag_result_data["name"],
                "reason": tag_result_data["classification_rationale"],
            },
        )
    return Command(
        update={
            "tag_result": tag_result_data,
        },
        goto="score",
    )
