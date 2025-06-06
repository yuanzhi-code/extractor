import logging
import random
import threading
from dataclasses import dataclass, field
from typing import Any, Optional

from .litellm_factory import LiteLLMChatModel, ModelConfig

logger = logging.getLogger(__name__)


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


@dataclass
class ModelPool:
    """模型池"""

    name: str
    description: str = ""
    models: list[ModelConfig] = field(default_factory=list)
    load_balance_strategy: str = "round_robin"
    pool_config: PoolConfig = field(default_factory=PoolConfig)

    # 运行时状态
    _round_robin_counter: int = 0
    _model_health: dict[str, bool] = field(default_factory=dict)
    _model_error_count: dict[str, int] = field(default_factory=dict)
    _circuit_breaker_until: dict[str, float] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def __post_init__(self):
        """初始化后处理"""
        for model in self.models:
            model_key = f"{model.provider}:{model.model}"
            self._model_health[model_key] = True
            self._model_error_count[model_key] = 0
            self._circuit_breaker_until[model_key] = 0.0

    def get_model(self) -> LiteLLMChatModel:
        """从池中获取一个模型实例"""
        if not self.models:
            raise ValueError(f"模型池 {self.name} 中没有可用的模型")

        # 过滤可用的模型
        available_models = self._get_healthy_models()
        if not available_models:
            # 如果没有健康的模型，尝试重置所有模型状态
            logger.warning(f"池 {self.name} 中没有健康的模型，重置状态")
            self._reset_all_models()
            available_models = self.models

        # 根据策略选择模型
        selected_model = self._select_model(available_models)
        logger.debug(f"从池 {self.name} 选择模型: {selected_model.model}")

        return LiteLLMChatModel(selected_model)

    def _get_healthy_models(self) -> list[ModelConfig]:
        """获取健康的模型列表"""
        import time

        current_time = time.time()
        healthy_models = []

        with self._lock:
            for model in self.models:
                model_key = f"{model.provider}:{model.model}"

                # 检查熔断器状态
                if current_time < self._circuit_breaker_until.get(model_key, 0):
                    continue

                # 检查健康状态
                if self._model_health.get(model_key, True):
                    healthy_models.append(model)

        return healthy_models

    def _select_model(self, available_models: list[ModelConfig]) -> ModelConfig:
        """根据负载均衡策略选择模型"""
        if len(available_models) == 1:
            return available_models[0]

        strategy = self.load_balance_strategy

        if strategy == "round_robin":
            with self._lock:
                index = self._round_robin_counter % len(available_models)
                self._round_robin_counter += 1
                return available_models[index]

        elif strategy == "random":
            return random.choice(available_models)

        elif strategy == "weighted_random":
            weights = [model.weight for model in available_models]
            return random.choices(available_models, weights=weights)[0]

        elif strategy == "least_used":
            # 选择错误次数最少的模型
            with self._lock:
                best_model = min(
                    available_models,
                    key=lambda m: self._model_error_count.get(
                        f"{m.provider}:{m.model}", 0
                    ),
                )
                return best_model

        else:
            logger.warning(f"未知的负载均衡策略: {strategy}, 使用random")
            return random.choice(available_models)

    def report_error(self, model: ModelConfig, error: Exception):
        """报告模型错误"""
        model_key = f"{model.provider}:{model.model}"

        with self._lock:
            self._model_error_count[model_key] = (
                self._model_error_count.get(model_key, 0) + 1
            )
            error_count = self._model_error_count[model_key]

            logger.warning(
                f"模型 {model_key} 错误计数: {error_count}, 错误: {error}"
            )

            # 检查是否需要触发熔断器
            if error_count >= self.pool_config.circuit_breaker_threshold:
                import time

                self._circuit_breaker_until[model_key] = (
                    time.time() + self.pool_config.circuit_breaker_timeout
                )
                self._model_health[model_key] = False
                logger.error(
                    f"模型 {model_key} 熔断器触发，将在 {self.pool_config.circuit_breaker_timeout} 秒后恢复"
                )

    def report_success(self, model: ModelConfig):
        """报告模型成功"""
        model_key = f"{model.provider}:{model.model}"

        with self._lock:
            # 重置错误计数和健康状态
            self._model_error_count[model_key] = 0
            self._model_health[model_key] = True
            self._circuit_breaker_until[model_key] = 0.0

    def _reset_all_models(self):
        """重置所有模型状态"""
        with self._lock:
            for model in self.models:
                model_key = f"{model.provider}:{model.model}"
                self._model_health[model_key] = True
                self._model_error_count[model_key] = 0
                self._circuit_breaker_until[model_key] = 0.0

    def get_status(self) -> dict[str, Any]:
        """获取池状态"""
        import time

        current_time = time.time()

        with self._lock:
            model_status = {}
            for model in self.models:
                model_key = f"{model.provider}:{model.model}"
                model_status[model_key] = {
                    "healthy": self._model_health.get(model_key, True),
                    "error_count": self._model_error_count.get(model_key, 0),
                    "circuit_breaker_active": current_time
                    < self._circuit_breaker_until.get(model_key, 0),
                    "circuit_breaker_until": self._circuit_breaker_until.get(
                        model_key, 0
                    ),
                }

        return {
            "name": self.name,
            "description": self.description,
            "total_models": len(self.models),
            "healthy_models": len(self._get_healthy_models()),
            "load_balance_strategy": self.load_balance_strategy,
            "model_status": model_status,
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
    ) -> LiteLLMChatModel:
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
        """报告模型错误"""
        pool_name = self._get_pool_for_node(node_name)
        if pool_name and pool_name in self.pools:
            self.pools[pool_name].report_error(model_config, error)

    def report_model_success(
        self, node_name: Optional[str], model_config: ModelConfig
    ):
        """报告模型成功"""
        pool_name = self._get_pool_for_node(node_name)
        if pool_name and pool_name in self.pools:
            self.pools[pool_name].report_success(model_config)

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
