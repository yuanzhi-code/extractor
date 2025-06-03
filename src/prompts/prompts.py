import os
from typing import Dict, List


def _model_specific_prompt(model_name: str | None) -> str:
    if model_name and "qwen3" in model_name.casefold():
        return "/no_think\n"
    return ""


def get_prompt(
    prompt_name: str,
    model_name: str = None,
) -> List[Dict]:
    dir_name = os.path.dirname(__file__)
    try:
        with open(os.path.join(dir_name, f"{prompt_name}.md"), "r") as f:
            return [
                {
                    "role": "system",
                    "content": _model_specific_prompt(model_name) + f.read(),
                }
            ]
    except Exception as e:
        raise ValueError(f"Prompt {prompt_name} not found")
