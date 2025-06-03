import json

from langchain_core.messages import BaseMessage


def pretty_response(response: BaseMessage):
    response.content = response.content.strip()
    if response.content.startswith("```json") and response.content.endswith(
        "```"
    ):
        response.content = response.content[len("```json") : -len("```")]


def get_response_property(response: BaseMessage, property_name: str):
    content = json.load(response.content)
    return content[property_name]
