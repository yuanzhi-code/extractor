import os
from typing import Dict


def get_prompt(
    prompt_name: str,
) -> Dict:
    dir_name = os.path.dirname(__file__)
    try:
        with open(os.path.join(dir_name, f"{prompt_name}.md"), "r") as f:
            return {
                "role": "system",
                "content": f.read(),
            }
    except Exception as e:
        raise ValueError(f"Prompt {prompt_name} not found")
