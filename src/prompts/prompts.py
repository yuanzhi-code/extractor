import os
from typing import Dict, List


def _get_prompt_content(prompt_name: str) -> str:
    dir_name = os.path.dirname(__file__)
    with open(os.path.join(dir_name, f"{prompt_name}.md"), "r") as f:
        return f.read()


def _specify_prompt_content(prompt_name: str, model_name: str) -> str:
    content = _get_prompt_content(prompt_name)
    if model_name and "qwen3" in model_name.casefold():
        return "/no_think\n" + content
    return content


def get_prompt(
    prompt_name: str,
    model_name: str = None,
) -> List[Dict]:
    try:
        content = _specify_prompt_content(prompt_name, model_name)
        return [
            {
                "role": "system",
                "content": content,
            }
        ]
    except Exception as e:
        raise ValueError(f"Prompt {prompt_name} not found")
