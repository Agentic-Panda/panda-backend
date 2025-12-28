from langchain_google_genai import ChatGoogleGenerativeAI

from panda.models.errors import InvalidAPIKey
from panda.models.llm import LLMProvider
from panda import Config

class LLMFactory:
    @staticmethod
    def create_client(provider: LLMProvider, **kwargs):
        if provider == LLMProvider.GEMINI:
            if not Config.GEMINI_API:
                raise InvalidAPIKey(f"No valid API Key have been provided to run Gemini")
            llm = ChatGoogleGenerativeAI(
                model=kwargs.get("model_name", "gemini-1.5-flash"),
                temperature=kwargs.get("temperature", 0.7),
                google_api_key=Config.GEMINI_API,
                max_retries=3,
                timeout=30,
            )   
            return llm
        else:
            raise ValueError(f"Unknown provider: {provider}")