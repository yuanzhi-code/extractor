import json
import logging

from src.config import config
from src.graph.state import State
from src.llms.factory import LLMFactory
from src.prompts.prompts import get_prompt

logger = logging.getLogger(__name__)


def score_node(state: State):
    logger.info("score node")
    prev_category = state.get("category")
    if prev_category is None:
        # return {"result": "No category found"}
        raise ValueError("No category found")

    if prev_category not in ["tech", "business", "experience"]:
        # return {"result": "Invalid category"}
        raise ValueError("Invalid category")

    model_provider = config.MODEL_PROVIDER
    llm = LLMFactory().get_llm(model_provider)
    message = get_prompt(f"scorer_{prev_category}", model_name=llm.model_name)
    message += [
        {
            "role": "user",
            "content": f"""
        content which need to be scored:
          {state['messages'][-1].content}
          """,
        }
    ]
    response = llm.invoke(message)
    response.content = response.content.strip()
    # for some models, the response is wrapped in ```json, so we need to remove it
    if response.content.startswith("```json") and response.content.endswith(
        "```"
    ):
        response.content = response.content[len("```json") : -len("```")]
    with open("response-score.json", "w", encoding="utf-8") as f:
        f.write(response.content)
    return {"result": response}
