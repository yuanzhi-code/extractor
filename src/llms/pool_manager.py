import logging
from dataclasses import dataclass, field
import os
from typing import Any, Optional

import litellm
from langchain_core.messages import AIMessage, BaseMessage
from litellm import Router

from .litellm_factory import ModelConfig

logger = logging.getLogger(__name__)

# 配置 LiteLLM 日志级别，避免重复日志
litellm.set_verbose = False
litellm_logger = logging.getLogger("LiteLLM")
litellm_logger.setLevel(logging.WARNING)  # 只显示警告和错误

# 禁用 LiteLLM Router 的日志
router_logger = logging.getLogger("LiteLLM Router")
router_logger.setLevel(logging.WARNING)

litellm.success_callback = ["langfuse"]
litellm.failure_callback = ["langfuse"]

@dataclass
class PoolConfig:
    """模型池配置"""

    max_retries: int = 3
    timeout: int = 30
    concurrent_limit: int = 10
    circuit_breaker_threshold: int = 5  # 熔断阈值
    circuit_breaker_timeout: int = 60  # 熔断恢复时间（秒）
    health_check_interval: int = 30  # 健康检查间隔（秒）
    extra_params: dict[str, Any] = field(default_factory=dict)


class LiteLLMRouterWrapper:
    """LiteLLM Router 的包装器，提供 LangChain 兼容的接口"""

    def __init__(self, router: Router, pool_name: str):
        self.router = router
        self.pool_name = pool_name

    def invoke(self, messages: list[BaseMessage], **kwargs) -> AIMessage:
        """调用模型，返回 AIMessage"""
        # 转换 LangChain 消息格式为 LiteLLM 格式
        litellm_messages = []
        for msg in messages:
            if hasattr(msg, "type") and hasattr(msg, "content"):
                # 映射 LangChain 角色到 OpenAI 格式
                role_mapping = {
                    "human": "user",
                    "user": "user",
                    "ai": "assistant",
                    "assistant": "assistant",
                    "system": "system",
                    "tool": "tool",
                }

                role = role_mapping.get(msg.type, "user")  # 默认为 user
                litellm_messages.append({"role": role, "content": msg.content})
            else:
                # 兼容其他格式
                litellm_messages.append({"role": "user", "content": str(msg)})

        # 调用 LiteLLM Router
        try:
            # 使用池名作为模型名，Router 会自动选择最佳部署
            response = self.router.completion(
                model=self.pool_name,  # Router 使用这个来找到对应的部署
                messages=litellm_messages,
                **kwargs,
            )

            # 转换回 LangChain 格式
            content = response.choices[0].message.content
            return AIMessage(content=content)

        except Exception as e:
            logger.exception("LiteLLM Router调用失败")
            raise


@dataclass
class ModelPool:
    """基于 LiteLLM Router 的模型池"""

    name: str
    description: str = ""
    models: list[ModelConfig] = field(default_factory=list)
    load_balance_strategy: str = "round_robin"
    pool_config: PoolConfig = field(default_factory=PoolConfig)

    # LiteLLM Router 实例
    _router: Optional[Router] = field(default=None, init=False)

    def __post_init__(self):
        """初始化 LiteLLM Router"""
        self._setup_router()

    def _setup_router(self):
        """设置 LiteLLM Router"""
        if not self.models:
            logger.warning(f"模型池 {self.name} 没有配置模型")
            return

        # 转换为 LiteLLM Router 格式
        model_list = []
        for model in self.models:
            # 构建模型配置
            model_config = {
                "model_name": self.name,  # 使用池名作为 model_name，让所有模型属于同一组
                "litellm_params": {
                    "model": (
                        f"{model.provider}/{model.model}"
                        if model.provider != "openai"
                        else f"openai/{model.model}"
                    ),
                    "api_key": model.api_key,
                    "api_base": model.api_base,
                    "temperature": model.temperature,
                    "timeout": model.timeout,
                },
            }
            
            # 添加 tpm/rpm 限制（如果指定）
            if model.tpm is not None:
                model_config["tpm"] = model.tpm
            if model.rpm is not None:
                model_config["rpm"] = model.rpm

            # 添加权重（如果支持）
            if hasattr(model, "weight") and model.weight > 0:
                model_config["litellm_params"]["weight"] = model.weight

            model_list.append(model_config)

        # 创建 Router
        router_settings = {
            "routing_strategy": self._convert_strategy(
                self.load_balance_strategy
            ),
            "model_list": model_list,
            "redis_host": None,  # 暂时不使用 Redis
            "redis_password": None,
            "redis_port": None,
            "timeout": self.pool_config.timeout,
            "num_retries": self.pool_config.max_retries,
            "cooldown_time": self.pool_config.circuit_breaker_timeout,
            "default_max_parallel_requests": self.pool_config.concurrent_limit,
        }

        try:
            # 添加调试和日志控制
            router_settings.update({
                "set_verbose": False,  # 禁用详细日志
                "debug_level": "ERROR",  # 只显示错误级别日志
            })
            
            self._router = Router(**router_settings)
            logger.info(
                f"为池 {self.name} 创建 LiteLLM Router，包含 {len(model_list)} 个模型"
            )
        except Exception as e:
            logger.exception("创建 LiteLLM Router 失败")
            raise

    def _convert_strategy(self, strategy: str) -> str:
        """转换负载均衡策略"""
        strategy_mapping = {
            "round_robin": "simple-shuffle",
            "random": "simple-shuffle",
            "weighted_random": "latency-based-routing",
            "least_used": "usage-based-routing-v2",
        }

        return strategy_mapping.get(strategy, "simple-shuffle")

    def get_model(self) -> LiteLLMRouterWrapper:
        """获取模型实例"""
        if not self._router:
            raise ValueError(f"模型池 {self.name} 的 Router 未初始化")

        return LiteLLMRouterWrapper(self._router, self.name)

    def get_status(self) -> dict[str, Any]:
        """获取池状态"""
        if not self._router:
            return {
                "name": self.name,
                "description": self.description,
                "status": "not_initialized",
                "total_models": len(self.models),
            }

        # 获取 Router 状态
        try:
            router_health = self._router.health_check()
            healthy_models = sum(
                1
                for model_health in router_health.values()
                if model_health.get("status") == "healthy"
            )
        except:
            healthy_models = 0

        return {
            "name": self.name,
            "description": self.description,
            "status": "active",
            "total_models": len(self.models),
            "healthy_models": healthy_models,
            "load_balance_strategy": self.load_balance_strategy,
            "router_strategy": self._convert_strategy(
                self.load_balance_strategy
            ),
        }


class PoolManager:
    """模型池管理器"""

    def __init__(self):
        self.pools: dict[str, ModelPool] = {}
        self.node_pool_mapping: dict[str, str] = {}
        self.default_pool: Optional[str] = None

    def create_pool(
        self,
        name: str,
        models: list[ModelConfig],
        description: str = "",
        load_balance_strategy: str = "round_robin",
        pool_config: Optional[PoolConfig] = None,
    ) -> ModelPool:
        """创建一个新的模型池"""
        if pool_config is None:
            pool_config = PoolConfig()

        pool = ModelPool(
            name=name,
            description=description,
            models=models,
            load_balance_strategy=load_balance_strategy,
            pool_config=pool_config,
        )

        self.pools[name] = pool
        logger.info(
            f"创建模型池 {name}: {len(models)} 个模型, 策略: {load_balance_strategy}"
        )
        return pool

    def set_node_pool(self, node_name: str, pool_name: str):
        """设置节点使用的池"""
        if pool_name not in self.pools:
            raise ValueError(f"池 {pool_name} 不存在")

        self.node_pool_mapping[node_name] = pool_name
        logger.info(f"节点 {node_name} 绑定到池 {pool_name}")

    def set_default_pool(self, pool_name: str):
        """设置默认池"""
        if pool_name not in self.pools:
            raise ValueError(f"池 {pool_name} 不存在")

        self.default_pool = pool_name
        logger.info(f"设置默认池: {pool_name}")

    def get_model_for_node(
        self, node_name: Optional[str] = None
    ) -> LiteLLMRouterWrapper:
        """为指定节点获取模型"""
        pool_name = self._get_pool_for_node(node_name)
        if not pool_name:
            raise ValueError(f"没有为节点 {node_name} 找到可用的池")

        pool = self.pools[pool_name]
        try:
            model_instance = pool.get_model()
            logger.info(f"为节点 {node_name} 从池 {pool_name} 获取模型")
            return model_instance
        except Exception as e:
            logger.exception(f"从池 {pool_name} 获取模型失败")
            raise

    def _get_pool_for_node(self, node_name: Optional[str]) -> Optional[str]:
        """获取节点对应的池名称"""
        if node_name and node_name in self.node_pool_mapping:
            return self.node_pool_mapping[node_name]
        return self.default_pool

    def report_model_error(
        self,
        node_name: Optional[str],
        model_config: ModelConfig,
        error: Exception,
    ):
        """报告模型错误 - LiteLLM Router 自动处理"""
        logger.debug(
            f"模型错误报告: {model_config.provider}:{model_config.model} - {error}"
        )
        # LiteLLM Router 自动处理错误和熔断
        pass

    def report_model_success(
        self, node_name: Optional[str], model_config: ModelConfig
    ):
        """报告模型成功 - LiteLLM Router 自动处理"""
        logger.debug(
            f"模型成功报告: {model_config.provider}:{model_config.model}"
        )
        # LiteLLM Router 自动处理成功状态
        pass

    def list_pools(self) -> dict[str, dict[str, Any]]:
        """列出所有池的状态"""
        return {name: pool.get_status() for name, pool in self.pools.items()}

    def get_pool_mapping(self) -> dict[str, Any]:
        """获取节点池映射关系"""
        return {
            "node_mapping": self.node_pool_mapping.copy(),
            "default_pool": self.default_pool,
            "available_pools": list(self.pools.keys()),
        }

    def clear_all(self):
        """清空所有池和映射"""
        self.pools.clear()
        self.node_pool_mapping.clear()
        self.default_pool = None
        logger.info("已清空所有模型池")


# 创建全局池管理器实例
pool_manager = PoolManager()
