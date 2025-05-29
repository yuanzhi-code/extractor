import logging

from langchain_openai import ChatOpenAI
from langchain_community.embeddings import OpenAIEmbeddings

from src.config import config

logger = logging.getLogger(__name__)


class LLMFactory:
    _factory_registry_embedding = {
        "siliconflow": {
            "base_url": "https://api.siliconflow.cn/v1",
            "model": config.SILICONFLOW_EMBEDDING_MODEL,
            "api_key": config.SILICONFLOW_API_KEY,
        },
    }

    _factory_registry_chat = {
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

    supported_llms = _factory_registry_chat.keys()

    def get_llm(self, llm_type: str):
        cfg = self._factory_registry_chat.get(llm_type)
        if not cfg:
            raise ValueError(f"Unsupported LLM type: {llm_type}")
        logger.info(f"Using LLM: {llm_type}/{cfg.get('model')}")
        return ChatOpenAI(**cfg)

    def get_embedding_model(self, llm_type: str):
        cfg = self._factory_registry_embedding.get(llm_type)
        if not cfg:
            raise ValueError(f"Unsupported LLM type: {llm_type}")
        logger.info(f"Using Embedding Model: {llm_type}/{cfg.get('model')}")
        return OpenAIEmbeddings(**cfg)

