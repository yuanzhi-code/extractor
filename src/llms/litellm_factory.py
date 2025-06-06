import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from langchain_core.messages import AIMessage
from litellm import completion

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """单个模型配置"""

    model: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    api_version: Optional[str] = None
    temperature: float = 0.0
    timeout: int = 30
    weight: int = 1  # 负载均衡权重
    provider: Optional[str] = None
    extra_params: dict[str, Any] = field(default_factory=dict)


class LiteLLMChatModel:
    """基于LiteLLM的简化ChatModel实现"""

    def __init__(self, model_config: ModelConfig):
        self._llm_config = model_config

    @property
    def llm_config(self) -> ModelConfig:
        """获取模型配置"""
        return self._llm_config

    def invoke(self, input_messages, **kwargs):
        """调用模型生成响应"""
        try:
            # 处理输入消息格式
            if isinstance(input_messages, str):
                litellm_messages = [{"role": "user", "content": input_messages}]
            elif isinstance(input_messages, list):
                litellm_messages = []
                for msg in input_messages:
                    if isinstance(msg, dict):
                        litellm_messages.append(msg)
                    elif hasattr(msg, "role") and hasattr(msg, "content"):
                        litellm_messages.append(
                            {"role": msg.role, "content": msg.content}
                        )
                    elif hasattr(msg, "content"):
                        # langchain消息对象
                        role = self._get_role_from_message(msg)
                        litellm_messages.append(
                            {"role": role, "content": msg.content}
                        )
                    else:
                        raise ValueError(f"不支持的消息格式: {type(msg)}")
            else:
                raise ValueError(f"不支持的输入格式: {type(input_messages)}")

            # 构建LiteLLM格式的模型名称（使用openai/前缀表示OpenAI兼容的端点）
            if self._llm_config.provider == "openai":
                full_model_name = f"openai/{self._llm_config.model}"
            else:
                full_model_name = self._llm_config.model

            # 准备API调用参数
            params = {
                "model": full_model_name,
                "messages": litellm_messages,
                "temperature": self._llm_config.temperature,
                "timeout": self._llm_config.timeout,
                **self._llm_config.extra_params,
                **kwargs,
            }

            if self._llm_config.api_key:
                params["api_key"] = self._llm_config.api_key
            if self._llm_config.api_base:
                params["api_base"] = self._llm_config.api_base
            if self._llm_config.api_version:
                params["api_version"] = self._llm_config.api_version

            # 调用LiteLLM
            response = completion(**params)

            # 返回简化的AIMessage对象
            content = response.choices[0].message.content
            return AIMessage(content=content)

        except Exception as e:
            logger.exception("LiteLLM调用失败")
            raise

    def _get_role_from_message(self, msg) -> str:
        """从langchain消息对象获取角色"""
        if hasattr(msg, "role"):
            return msg.role

        role_mapping = {
            "HumanMessage": "user",
            "SystemMessage": "system",
            "AIMessage": "assistant",
        }

        return role_mapping.get(msg.__class__.__name__, "user")
