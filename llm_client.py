import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class LLMClient:
    """LLM 客户端封装，支持 DeepSeek 及其他 OpenAI 兼容接口。"""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError(
                "未找到 DEEPSEEK_API_KEY。请在 .env 文件或系统环境变量中设置 DEEPSEEK_API_KEY。"
            )

        self.base_url = base_url or os.getenv(
            "DEEPSEEK_BASE_URL", "https://api.deepseek.com"
        )
        self.model = model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    def chat(self, messages: list[dict], tools: list[dict] | None = None):
        """向模型发起聊天请求。
        
        Args:
            messages: 当前对话历史列表
            tools: 工具定义列表 (Function Calling schemas)
            
        Returns:
            模型返回的 ChatCompletionMessage 对象
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message
