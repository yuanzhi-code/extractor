"""
硅基流动客户端实现
"""

from typing import Any, Dict, List, Optional

from openai import OpenAI


class SiliconFlowClient:
    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-8B",
        api_key: Optional[str] = None,
        base_url: str = "https://api.siliconflow.cn/v1",
    ):
        """
        初始化硅基流动客户端

        Args:
            model_name: 模型名称，默认为Qwen/Qwen3-8B
            api_key: API密钥，如果为None则从环境变量获取
            base_url: API基础URL
        """
        self.model_name = model_name
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        生成文本响应

        Args:
            prompt: 输入提示
            temperature: 温度参数，控制随机性
            max_tokens: 最大生成token数
            stop: 停止序列列表
            **kwargs: 其他参数

        Returns:
            包含生成结果的字典
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                stop=stop,
                **kwargs,
            )
            return {
                "text": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                "model": response.model,
            }
        except Exception as e:
            raise Exception(f"生成文本时发生错误: {str(e)}")

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        进行对话

        Args:
            messages: 消息历史列表
            temperature: 温度参数
            max_tokens: 最大生成token数
            stop: 停止序列列表
            **kwargs: 其他参数

        Returns:
            包含生成结果的字典
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stop=stop,
                **kwargs,
            )
            return {
                "text": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                "model": response.model,
            }
        except Exception as e:
            raise Exception(f"对话生成时发生错误: {str(e)}")
