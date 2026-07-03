import httpx

class APIClient:
    def __init__(self, api_key: str, base_url: str, model: str = "gpt-3.5-turbo"):
        """
        初始化 API 客户端。
        
        :param api_key: API 密钥
        :param base_url: API 基础地址 (例如: https://apihub.agnes-ai.com)
        :param model: 要使用的模型名称，默认为 "gpt-3.5-turbo"
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model = model  # 保存传入的模型名称
        self.endpoint = "/v1/chat/completions"

        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )

    async def send_message(self, prompt: str) -> str:
        """
        发送消息到自定义 API 并获取回复。
        """
        payload = {
            "model": self.model,  # 使用初始化时传入的模型名称
            "messages": [{"role": "user", "content": prompt}]
        }
        
        try:
            url = f"{self.base_url}{self.endpoint}"
            response = await self.client.post(url, json=payload, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
                
        except Exception as e:
            return f"Error: {str(e)}"