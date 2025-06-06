"""
llms package - 基于池管理的统一LLM配置系统
"""

from .litellm_factory import LiteLLMChatModel, ModelConfig
from .pool_config_manager import PoolConfigManager, pool_config_manager
from .pool_manager import ModelPool, PoolConfig, PoolManager, pool_manager
from .unified_manager import UnifiedLLMManager, unified_llm_manager

# 池管理相关实例
pool_manager = pool_manager
pool_config_manager = pool_config_manager
unified_llm_manager = unified_llm_manager

# 向后兼容的别名
llm_manager = unified_llm_manager

__all__ = [
    "LiteLLMChatModel",
    "ModelConfig",
    "ModelPool",
    "PoolConfig",
    "PoolConfigManager",
    "PoolManager",
    "UnifiedLLMManager",
    "llm_manager",
    "pool_config_manager",
    "pool_manager",
    "unified_llm_manager",
]
