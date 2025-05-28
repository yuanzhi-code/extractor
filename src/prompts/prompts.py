import os
from typing import Dict, List


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
                    "content": (
                        "/no_think\n"
                        if model_name and "qwen3" in model_name.casefold()
                        else ""
                    )
                    + f.read(),
                }
            ]
    except Exception as e:
        raise ValueError(f"Prompt {prompt_name} not found")
