from langchain_openai import ChatOpenAI

from src.config.app_config import AppConfig


class LLMFactory:
    config = AppConfig()
    _factory_registry = {
        "ollama": {
            "base_url": config.OLLAMA_URL,
            "model": config.OLLAMA_MODEL,
            "api_key":"a"
        },
        "siliconflow": {
            "base_url": "https://api.siliconflow.cn/v1",
            "model": config.SILICONFLOW_MODEL,
            "api_key": config.SILICONFLOW_API_KEY,
        },
        "deepseek": {
            "base_url": "https://api.deepseek.com/v1",
            "model": config.DEEPSEEK_MODEL,
            "api_key": config.DEEPSEEK_API_KEY,
        },
    }

    def get_llm(self, llm_type: str):
        cfg = self.get_llm_cfg(llm_type)
        if not cfg:
            raise ValueError(f"Unsupported LLM type: {llm_type}")
        
        print(cfg)

        return ChatOpenAI(**cfg)

    def get_llm_cfg(self, llm_type: str):
        cfg = self._factory_registry.get(llm_type)
        return cfg
