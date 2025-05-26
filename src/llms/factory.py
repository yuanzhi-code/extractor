from langchain_ollama import OllamaLLM
from langchain_openai import ChatOpenAI

from config.app_config import AppConfig

from .ollama_client import OllamaClient
from .siliconflow_client import SiliconFlowClient


class LLMFactory:
    _factory_registry = {
        "ollama": {
            "base_url": AppConfig.OLLAMA_URL,
            "model": AppConfig().OLLAMA_MODEL,
        },
        "siliconflow": {
            "base_url": "https://api.siliconflow.cn/v1",
            "model": AppConfig().SILICONFLOW_MODEL,
            "api_key": AppConfig().SILICONFLOW_API_KEY,
        },
    }

    def get_llm(self, llm_type: str):
        cfg = self.get_llm_cfg(llm_type)
        if not cfg:
            raise ValueError(f"Unsupported LLM type: {llm_type}")

        return ChatOpenAI(model=cfg)

    def get_llm_cfg(self, llm_type: str):
        cfg = self._factory_registry.get(llm_type)
        return cfg
