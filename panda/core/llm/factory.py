from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from panda.models.errors import InvalidAPIKey
from panda.models.llm import LLMProvider
from panda import Config


class LLMFactory:
    @staticmethod
    def create_client(provider: LLMProvider, **kwargs):
        if provider == LLMProvider.GEMINI:
            if not Config.GEMINI_API:
                raise InvalidAPIKey("No valid API Key has been provided to run Gemini")

            return ChatGoogleGenerativeAI(
                model=kwargs.get("model_name", "gemini-1.5-flash"),
                temperature=kwargs.get("temperature", 0.7),
                google_api_key=Config.GEMINI_API,
                max_retries=3,
                timeout=30,
            )

        elif provider == LLMProvider.OPENROUTER:
            if not Config.OPENROUTER_API_KEY:
                raise InvalidAPIKey("No valid API Key has been provided to run OpenRouter")

            return ChatOpenAI(
                model=kwargs.get("model_name", "xiaomi/mimo-v2-flash:free"),
                temperature=kwargs.get("temperature", 0.7),
                api_key=Config.OPENROUTER_API_KEY,
                base_url="https://openrouter.ai/api/v1",
                max_retries=3,
                timeout=30,
                default_headers={
                    "HTTP-Referer": kwargs.get("referer", "https://test.itsvinayak.eu.org"),
                    "X-Title": kwargs.get("app_name", "Panda"),
                },
            )

        else:
            raise ValueError(f"Unknown provider: {provider}")
