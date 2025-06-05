import logging
from typing import Optional

from langchain_openai import ChatOpenAI

from src.config import config

logger = logging.getLogger(__name__)


class LLMFactory:
    """
    llm factory
    Args:
        llm_type: str
        model: Optional[str]
    Returns:
        ChatOpenAI: llm instance
    """
    _factory_registry = {
        "ollama": {
            "base_url": config.OLLAMA_URL,
            "model": config.OLLAMA_MODEL,
            "api_key": "a",
            "temperature": 0,  # localhost ollama does not need api key, but ChatOpenAI requires it
        },
        "siliconflow": {
            "base_url": "https://api.siliconflow.cn/v1",
            "model": config.SILICONFLOW_MODEL,
            "api_key": config.SILICONFLOW_API_KEY,
            "temperature": 0,
        },
        "deepseek": {
            "base_url": "https://api.deepseek.com/v1",
            "model": config.DEEPSEEK_MODEL,
            "api_key": config.DEEPSEEK_API_KEY,
            "temperature": 0,
        },
    }

    supported_llms = _factory_registry.keys()

    def get_llm(self, llm_type: str, model: Optional[str] = None) -> ChatOpenAI:
        """
        get llm instance
        Args:
            llm_type: str
            model: Optional[str]
        Returns:
            ChatOpenAI: llm instance
        """
        cfg = self._get_llm_cfg(llm_type)
        if not cfg:
            raise ValueError(f"Unsupported LLM type: {llm_type}")
        if model is not None:
            cfg["model"] = model
        logger.info(f"Using LLM: {llm_type}/{cfg.get('model')}")
        llm = ChatOpenAI(**cfg)
        return llm

    def _get_llm_cfg(self, llm_type: str):
        cfg = self._factory_registry.get(llm_type)
        return cfg
