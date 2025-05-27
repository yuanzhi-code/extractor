import langgraph
import langgraph.prebuilt

from src.llms.factory import LLMFactory


def create_agent(
    name: str, llm_type: str = "ollama", prompt: str = None, tools: list = []
):
    """
    创建一个 ReAct agent

    Args:
        name: agent 名称
        llm_type: LLM 类型 ("ollama" 或 "siliconflow")
        prompt: 提示词
        tools: 工具列表

    Returns:
        CompiledGraph: 编译后的 agent 图
    """
    # 创建 LLM 适配器
    model = LLMFactory().get_llm(llm_type)

    # 使用 langgraph 的预构建 react agent
    return langgraph.prebuilt.create_react_agent(name, model, tools, prompt)
