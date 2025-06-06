import logging
from typing import Optional

from .pool_config_manager import pool_config_manager
from .pool_manager import LiteLLMRouterWrapper, pool_manager

logger = logging.getLogger(__name__)


class UnifiedLLMManager:
    """统一的LLM管理器，专注于池管理系统"""

    def __init__(self):
        self.initialized = False

    def initialize(self):
        """初始化管理器"""
        # 初始化池配置
        pool_config_manager.initialize()

        # 检查是否有池配置
        pools = pool_manager.list_pools()
        if pools:
            self.initialized = True
            logger.info(f"池管理系统初始化成功，共 {len(pools)} 个池")
        else:
            # 如果没有池配置，这是一个错误状态
            logger.error("池管理系统初始化失败：没有找到任何池配置")
            raise RuntimeError(
                "LLM系统需要池配置才能运行。请配置 config/llm_pools.yaml 文件。"
            )

    def get_llm(
        self,
        node_name: Optional[str] = None,
    ) -> LiteLLMRouterWrapper:
        """
        获取LLM实例

        Args:
            node_name: 节点名称
            llm_type: LLM类型（已废弃，保留用于兼容性）
            model: 模型名称（已废弃，保留用于兼容性）

        Returns:
            LiteLLM模型实例

        Raises:
            RuntimeError: 如果系统未初始化或池系统获取失败
        """
        if not self.initialized:
            raise RuntimeError(
                "LLM管理器尚未初始化，请先调用 initialize() 方法"
            )

        try:
            model_instance = pool_manager.get_model_for_node(node_name)
            logger.debug(f"从池为节点 {node_name} 获取LiteLLM Router模型")

            # LiteLLM Router 自动处理监控，无需额外包装
            return model_instance
        except Exception as e:
            logger.exception(f"从池系统获取模型失败，节点: {node_name}")
            raise RuntimeError(
                f"无法从池系统获取模型（节点: {node_name}）。"
                f"请检查池配置和节点映射。错误详情: {e}"
            ) from e

    def is_using_pools(self) -> bool:
        """是否在使用池系统（总是返回True，因为只支持池系统）"""
        return self.initialized

    def is_using_litellm(self) -> bool:
        """是否在使用LiteLLM（总是返回True，因为池系统基于LiteLLM）"""
        return self.initialized

    def get_config_info(self) -> dict:
        """获取配置信息"""
        if not self.initialized:
            return {
                "type": "uninitialized",
                "error": "LLM管理器尚未初始化",
                "message": "请配置池系统后重新初始化",
            }

        pools_status = pool_manager.list_pools()
        pool_mapping = pool_manager.get_pool_mapping()
        return {
            "type": "pools",
            "pools_count": len(pools_status),
            "pools": pools_status,
            "node_mapping": pool_mapping,
            "initialized": True,
        }

    def get_pool_status(self) -> dict:
        """获取池状态"""
        if not self.initialized:
            return {"error": "LLM管理器尚未初始化"}

        return {
            "pools": pool_manager.list_pools(),
            "mapping": pool_manager.get_pool_mapping(),
        }

    def reload_config(self):
        """重新加载配置"""
        logger.info("重新加载池配置...")

        # 清空池配置
        pool_manager.clear_all()

        # 重新初始化
        self.initialized = False
        self.initialize()

        logger.info("配置重新加载完成")


# 创建全局实例
unified_llm_manager = UnifiedLLMManager()
