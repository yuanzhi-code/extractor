import json
import logging
from typing import Any, Optional

from langchain_core.messages import BaseMessage
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def pretty_response(response: BaseMessage):
    response.content = response.content.strip()
    if response.content.startswith("```json") and response.content.endswith(
        "```"
    ):
        response.content = response.content[len("```json") : -len("```")]


def get_response_property(response: BaseMessage, property_name: str):
    content = json.loads(response.content)
    return content[property_name]


def parse_llm_json_response(
    response_text: str, default: Optional[dict] = None
) -> dict:
    """
    解析LLM的JSON响应，处理markdown代码块
    Args:
        response_text: LLM的文本响应
        default: 解析失败时返回的默认值，默认为空字典
    Returns:
        dict: 解析后的字典
    """
    if default is None:
        default = {}

    try:
        if isinstance(response_text, str):
            # 清理可能的markdown代码块标记
            cleaned_text = response_text.strip()
            cleaned_text = cleaned_text.removeprefix("```json")
            cleaned_text = cleaned_text.removesuffix("```")
            cleaned_text = cleaned_text.strip()

            # 处理多个JSON对象的情况，只取第一个
            if cleaned_text.count("{") > 1:
                logger.warning("检测到多个JSON对象，只使用第一个")
                # 找到第一个完整的JSON对象
                brace_count = 0
                first_json_end = -1
                for i, char in enumerate(cleaned_text):
                    if char == "{":
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            first_json_end = i + 1
                            break

                if first_json_end > 0:
                    cleaned_text = cleaned_text[:first_json_end]

            return json.loads(cleaned_text)
        else:
            return response_text if isinstance(response_text, dict) else default
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON response: {e}")
        logger.warning(f"Response content: {response_text}")
        return default
    except Exception as e:
        logger.warning(f"Unexpected error parsing response: {e}")
        return default


def extract_scorer_fields(response_text: str) -> tuple[str, str]:
    """
    从LLM响应文本中提取score和summary字段
    Args:
        response_text: LLM的文本响应
    Returns:
        tuple[str, str]: (score, summary)
    """
    data = parse_llm_json_response(response_text, {})
    score = data.get("tag", "")
    summary = data.get("summary", "")
    return score, summary


def extract_category_from_review(
    response_data: dict, tag_result_data: dict
) -> str:
    """
    从审查结果中提取category
    Args:
        response_data: TaggerReviewResult响应字典
        tag_result_data: 原始TagResult字典
    Returns:
        str: 提取的category名称
    """
    try:
        # 检查是否有新的分类建议
        if response_data.get("comment") and isinstance(
            response_data["comment"], dict
        ):
            return response_data["comment"].get("name", "other")
        elif response_data.get("approved", False):
            # 如果审核通过，使用原始tag_result
            return tag_result_data.get("name", "other")
        else:
            # 审核不通过且没有新建议，使用默认值
            return "other"
    except Exception as e:
        logger.exception("Failed to extract category from review response:")
        return "other"


def upsert_record(
    session: Session,
    model_class: type,
    filter_kwargs: dict[str, Any],
    update_kwargs: dict[str, Any],
    create_kwargs: Optional[dict[str, Any]] = None,
) -> tuple[Any, bool]:
    """
    通用的upsert操作：如果记录存在则更新，不存在则创建
    Args:
        session: SQLAlchemy会话
        model_class: 模型类
        filter_kwargs: 用于查询现有记录的过滤条件
        update_kwargs: 要更新的字段
        create_kwargs: 创建新记录时的额外字段，如果为None则使用filter_kwargs + update_kwargs
    Returns:
        tuple[record, created]: (记录对象, 是否为新创建)
    """
    # 查询现有记录
    existing = session.query(model_class).filter_by(**filter_kwargs).first()

    if existing:
        # 更新现有记录
        for key, value in update_kwargs.items():
            setattr(existing, key, value)
        return existing, False
    else:
        # 创建新记录
        if create_kwargs is None:
            create_kwargs = {**filter_kwargs, **update_kwargs}
        else:
            create_kwargs = {**filter_kwargs, **update_kwargs, **create_kwargs}

        new_record = model_class(**create_kwargs)
        session.add(new_record)
        return new_record, True
