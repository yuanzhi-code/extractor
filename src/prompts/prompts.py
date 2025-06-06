from typing import Optional

from .templates import scorer_prompt, tagger_prompt, tagger_review_prompt


def _model_specific_prompt(model_name: str | None) -> str:
    if model_name and "qwen3" in model_name.casefold():
        return "/no_think\n"
    return ""


def get_prompt(
    prompt_name: str,
    model_name: Optional[str] = None,
    **kwargs,
) -> list[dict]:
    _model_prompt_map = {
        "tagger": tagger_prompt,
        "tagger_review": tagger_review_prompt,
        "scorer": scorer_prompt,
    }
    if prompt_name not in _model_prompt_map:
        raise ValueError(f"Prompt {prompt_name} not found")
    return [
        {
            "role": "system",
            "content": _model_specific_prompt(model_name).format(**kwargs)
            + _model_prompt_map[prompt_name],
        }
    ]
