"""
Ollama client implementation using LiteLLM
"""
from typing import Optional, Dict, Any, List
import litellm
from litellm import completion

class OllamaClient:
    def __init__(self, model_name: str = "qwen3:4b", base_url: str = "http://localhost:11434"):
        """
        初始化Ollama客户端
        
        Args:
            model_name: Ollama模型名称，默认为qwen3:4b
            base_url: Ollama服务的基础URL，默认为本地地址
        """
        self.model_name = model_name
        self.base_url = base_url
        litellm.set_verbose = True  # 启用详细日志
        
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
        **kwargs
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
            response = completion(
                model=f"ollama/{self.model_name}",
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                stop=stop,
                api_base=self.base_url,
                **kwargs
            )
            return {
                "text": response.choices[0].message.content,
                "usage": response.usage,
                "model": response.model
            }
        except Exception as e:
            raise Exception(f"生成文本时发生错误: {str(e)}")
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
        **kwargs
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
            response = completion(
                model=f"ollama/{self.model_name}",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stop=stop,
                api_base=self.base_url,
                **kwargs
            )
            return {
                "text": response.choices[0].message.content,
                "usage": response.usage,
                "model": response.model
            }
        except Exception as e:
            raise Exception(f"对话生成时发生错误: {str(e)}")

if __name__ == "__main__":
    # 创建客户端实例
    client = OllamaClient(model_name="qwen3:4b")

    # 单次生成
    response = client.generate("你好，请介绍一下自己")
    print(response)

    # 多轮对话
    messages = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！有什么我可以帮你的吗？"},
        {"role": "user", "content": "请介绍一下你自己"}
    ]
    response = client.chat(messages)
    print(response)