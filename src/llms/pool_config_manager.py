import logging
from pathlib import Path
from typing import Any

import yaml

from .litellm_factory import ModelConfig
from .pool_manager import PoolConfig, pool_manager

logger = logging.getLogger(__name__)


class PoolConfigManager:
    """基于池的LLM配置管理器"""

    def __init__(self):
        self.config_file_path = Path("config/llm_pools.yaml")

    def load_from_file(self) -> bool:
        """从配置文件加载池配置"""
        if not self.config_file_path.exists():
            logger.error("池配置文件不存在")
            return False

        try:
            with open(self.config_file_path, encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            # 验证配置
            errors = self.validate_config(config_data)
            if errors:
                logger.error(f"池配置文件验证失败: {errors}")
                return False

            # 清空现有配置
            pool_manager.clear_all()

            # 解析供应商和模型定义
            providers_config = config_data.get("providers", {})
            model_registry = self._build_model_registry(providers_config)

            # 加载池配置
            pools_config = config_data.get("pools", {})
            for pool_name, pool_data in pools_config.items():
                models = self._resolve_pool_models(pool_data, model_registry)
                description = pool_data.get("description", "")
                load_balance_strategy = pool_data.get(
                    "load_balance_strategy", "round_robin"
                )

                # 解析池配置
                pool_config_data = pool_data.get("pool_config", {})
                pool_config = PoolConfig(
                    max_retries=pool_config_data.get("max_retries", 3),
                    timeout=pool_data.get(
                        "timeout", pool_config_data.get("timeout", 30)
                    ),
                    concurrent_limit=pool_config_data.get(
                        "concurrent_limit", 10
                    ),
                    circuit_breaker_threshold=pool_config_data.get(
                        "circuit_breaker_threshold", 5
                    ),
                    circuit_breaker_timeout=pool_config_data.get(
                        "circuit_breaker_timeout", 60
                    ),
                    health_check_interval=pool_config_data.get(
                        "health_check_interval", 30
                    ),
                    extra_params=pool_config_data.get("extra_params", {}),
                )

                pool_manager.create_pool(
                    name=pool_name,
                    models=models,
                    description=description,
                    load_balance_strategy=load_balance_strategy,
                    pool_config=pool_config,
                )
                logger.info(f"加载池 {pool_name}: {len(models)} 个模型")

            # 加载节点映射
            nodes_config = config_data.get("nodes", {})
            for node_name, node_data in nodes_config.items():
                if isinstance(node_data, str):
                    # 简单格式: "node": "pool_name"
                    pool_name = node_data
                elif isinstance(node_data, dict):
                    # 详细格式: "node": {"pool": "pool_name"}
                    pool_name = node_data.get("pool")
                else:
                    logger.warning(f"节点 {node_name} 配置格式错误")
                    continue

                if pool_name:
                    pool_manager.set_node_pool(node_name, pool_name)

            # 设置默认池
            default_pool = config_data.get("default_pool")
            if default_pool and default_pool in pools_config:
                pool_manager.set_default_pool(default_pool)
            elif pools_config:
                # 如果没有指定默认池，使用第一个池
                first_pool = list(pools_config.keys())[0]
                pool_manager.set_default_pool(first_pool)
                logger.info(f"自动设置默认池: {first_pool}")

            return True

        except Exception as e:
            logger.exception("加载池配置文件失败")
            return False

    def _build_model_registry(
        self, providers_config: dict
    ) -> dict[str, ModelConfig]:
        """构建模型注册表，将 provider:model 映射到ModelConfig"""
        model_registry = {}

        for provider_name, provider_data in providers_config.items():
            api_base = provider_data.get("api_base")
            api_key = provider_data.get("api_key")
            api_version = provider_data.get("api_version")
            provider_type = provider_data.get("provider", provider_name)

            models = provider_data.get("models", [])
            for model_data in models:
                model_name = model_data["model"]

                # 直接使用 provider:model 作为唯一标识
                model_key = f"{provider_name}:{model_name}"

                # 检查是否有重复
                if model_key in model_registry:
                    logger.warning(f"模型重复定义: '{model_key}' 将被覆盖")

                # 从模型级别或提供商级别获取配置
                model_config = ModelConfig(
                    model=model_name,
                    api_key=model_data.get("api_key", api_key),
                    api_base=model_data.get("api_base", api_base),
                    api_version=model_data.get("api_version", api_version),
                    temperature=model_data.get("temperature", 0.0),
                    timeout=model_data.get("timeout", 30),
                    weight=model_data.get("weight", 1),
                    provider=model_data.get("provider", provider_type),
                    tpm=model_data.get("tpm", 50000),
                    rpm=model_data.get("rpm", 1000),
                    extra_params=model_data.get("extra_params", {}),
                )

                model_registry[model_key] = model_config
                logger.debug(f"注册模型: {model_key}")

        return model_registry

    def _resolve_pool_models(
        self, pool_data: dict, model_registry: dict
    ) -> list[ModelConfig]:
        """解析池中的模型引用，返回ModelConfig列表"""
        models = []
        model_refs = pool_data.get("models", [])

        # 池级别的默认配置
        pool_temperature = pool_data.get("temperature")
        pool_timeout = pool_data.get("timeout")

        for model_ref in model_refs:
            # model_ref 应该是 "provider:model" 格式
            if model_ref not in model_registry:
                logger.error(f"模型 '{model_ref}' 在供应商配置中不存在")
                logger.info(f"可用模型: {list(model_registry.keys())}")
                continue

            # 复制基础模型配置
            base_config = model_registry[model_ref]
            model_config = ModelConfig(
                model=base_config.model,
                api_key=base_config.api_key,
                api_base=base_config.api_base,
                api_version=base_config.api_version,
                temperature=(
                    pool_temperature
                    if pool_temperature is not None
                    else base_config.temperature
                ),
                timeout=(
                    pool_timeout
                    if pool_timeout is not None
                    else base_config.timeout
                ),
                weight=base_config.weight,
                provider=base_config.provider,
                tpm=base_config.tpm,
                rpm=base_config.rpm,
                extra_params=base_config.extra_params,
            )
            models.append(model_config)

        return models

    def get_config_info(self) -> dict[str, Any]:
        """获取当前池配置信息"""
        return {
            "config_file": str(self.config_file_path),
            "file_exists": self.config_file_path.exists(),
            "pools": pool_manager.get_pool_names(),
            "default_pool": pool_manager.default_pool_name,
            "node_mappings": pool_manager.node_pool_mapping.copy(),
            "total_models": sum(
                len(pool.models) for pool in pool_manager.pools.values()
            ),
        }

    def validate_config(self, config_data: dict) -> list[str]:
        """验证配置数据并返回错误列表"""
        errors = []

        # 检查基本结构
        if "providers" not in config_data:
            errors.append("配置中缺少 'providers' 字段")
        if "pools" not in config_data:
            errors.append("配置中缺少 'pools' 字段")
            return errors

        # 验证供应商配置
        providers = config_data.get("providers", {})
        if not isinstance(providers, dict):
            errors.append("'providers' 必须是字典类型")
        else:
            provider_errors = self._validate_providers(providers)
            errors.extend(provider_errors)

        # 验证池配置
        pools = config_data["pools"]
        if not isinstance(pools, dict) or not pools:
            errors.append("'pools' 必须是非空字典")
            return errors

        # 建立模型引用集合用于引用检查
        model_refs = set()
        for provider_name, provider_data in providers.items():
            for model in provider_data.get("models", []):
                if "model" in model:
                    model_ref = f"{provider_name}:{model['model']}"
                    model_refs.add(model_ref)

        # 检查默认池
        default_pool = config_data.get("default_pool")
        if default_pool and default_pool not in pools:
            errors.append(f"默认池 '{default_pool}' 在 pools 中不存在")

        # 验证每个池
        for pool_name, pool_config in pools.items():
            pool_errors = self._validate_pool_config(
                pool_name, pool_config, model_refs
            )
            errors.extend(pool_errors)

        # 验证节点映射
        nodes = config_data.get("nodes", {})
        for node_name, node_config in nodes.items():
            if isinstance(node_config, str):
                pool_name = node_config
            elif isinstance(node_config, dict):
                pool_name = node_config.get("pool")
            else:
                errors.append(f"节点 '{node_name}' 配置格式错误")
                continue

            if pool_name and pool_name not in pools:
                errors.append(
                    f"节点 '{node_name}' 引用的池 '{pool_name}' 不存在"
                )

        return errors

    def _validate_providers(self, providers: dict) -> list[str]:
        """验证供应商配置"""
        errors = []

        if not providers:
            errors.append("至少需要配置一个供应商")
            return errors

        for provider_name, provider_data in providers.items():
            if not isinstance(provider_data, dict):
                errors.append(f"供应商 '{provider_name}' 配置必须是字典类型")
                continue

            # 检查模型配置
            models = provider_data.get("models", [])
            if not isinstance(models, list) or not models:
                errors.append(f"供应商 '{provider_name}' 必须包含至少一个模型")
                continue

            # 检查模型名称唯一性
            model_names = []
            for i, model in enumerate(models):
                if not isinstance(model, dict):
                    errors.append(
                        f"供应商 '{provider_name}' 的模型 {i} 必须是字典类型"
                    )
                    continue

                # 检查必需字段
                if "model" not in model:
                    errors.append(
                        f"供应商 '{provider_name}' 的模型 {i} 缺少 'model' 字段"
                    )
                    continue

                # 检查模型名称唯一性
                model_name = model.get("model")
                if model_name in model_names:
                    errors.append(
                        f"供应商 '{provider_name}' 中模型 '{model_name}' 重复"
                    )
                else:
                    model_names.append(model_name)

        return errors

    def _validate_pool_config(
        self, pool_name: str, pool_config: dict, valid_model_refs: set
    ) -> list[str]:
        """验证单个池配置"""
        errors = []

        if not isinstance(pool_config, dict):
            errors.append(f"池 '{pool_name}' 配置必须是字典类型")
            return errors

        # 检查模型引用
        models = pool_config.get("models", [])
        if not isinstance(models, list) or not models:
            errors.append(f"池 '{pool_name}' 必须包含至少一个模型引用")
        else:
            for model_ref in models:
                if not isinstance(model_ref, str):
                    errors.append(
                        f"池 '{pool_name}' 的模型引用必须是字符串类型"
                    )
                elif model_ref not in valid_model_refs:
                    errors.append(
                        f"池 '{pool_name}' 引用的模型 '{model_ref}' 不存在"
                    )

        # 检查负载均衡策略
        strategy = pool_config.get("load_balance_strategy", "round_robin")
        valid_strategies = [
            "round_robin",
            "random",
            "weighted_random",
            "least_used",
        ]
        if strategy not in valid_strategies:
            errors.append(
                f"池 '{pool_name}' 的负载均衡策略 '{strategy}' 无效，"
                f"支持的策略: {valid_strategies}"
            )

        # 验证池级别配置
        pool_settings = {
            "temperature": (0.0, 2.0),
            "timeout": (1, 300),
        }

        for setting, (min_val, max_val) in pool_settings.items():
            if setting in pool_config:
                value = pool_config[setting]
                if not isinstance(value, int | float):
                    errors.append(
                        f"池 '{pool_name}' 的 '{setting}' 必须是数值类型"
                    )
                elif not (min_val <= value <= max_val):
                    errors.append(
                        f"池 '{pool_name}' 的 '{setting}' 必须在 {min_val}-{max_val} 范围内"
                    )

        # 验证池配置参数
        pool_config_data = pool_config.get("pool_config", {})
        if pool_config_data:
            pool_errors = self._validate_pool_settings(
                pool_name, pool_config_data
            )
            errors.extend(pool_errors)

        return errors

    def _validate_pool_settings(
        self, pool_name: str, pool_settings: dict
    ) -> list[str]:
        """验证池设置参数"""
        errors = []

        # 数值型参数验证
        numeric_settings = {
            "max_retries": (1, 10),
            "timeout": (1, 300),
            "concurrent_limit": (1, 100),
            "circuit_breaker_threshold": (1, 50),
            "circuit_breaker_timeout": (10, 3600),
            "health_check_interval": (10, 300),
        }

        for setting, (min_val, max_val) in numeric_settings.items():
            if setting in pool_settings:
                value = pool_settings[setting]
                if not isinstance(value, int | float):
                    errors.append(
                        f"池 '{pool_name}' 的 '{setting}' 必须是数值类型"
                    )
                elif not (min_val <= value <= max_val):
                    errors.append(
                        f"池 '{pool_name}' 的 '{setting}' 必须在 {min_val}-{max_val} 范围内"
                    )

        return errors

    def initialize(self):
        """初始化池配置管理器"""
        # 只从文件加载，不再回退到环境变量
        if not self.load_from_file():
            raise RuntimeError(
                "未找到池配置文件 config/llm_pools.yaml。"
                "请配置池系统或使用示例文件创建配置：\n"
                "cp config/llm_pools.example.yaml config/llm_pools.yaml"
            )


# 创建全局实例
pool_config_manager = PoolConfigManager()
