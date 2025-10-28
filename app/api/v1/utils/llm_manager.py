from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain_openai import AzureChatOpenAI
from app.api.v1.utils.config import Config


class LLMManager:
    def __init__(self, config: Config, temperature: int = 0):
        self.conf = config
        self.llm = AzureChatOpenAI(
                azure_deployment= self.conf.ai_deployment_name,
                api_version= self.conf.ai_api_version,
                temperature= temperature,
                max_tokens= None,
                timeout= None,
                max_retries=2,
        )

    def connect(self):
        return self.llm