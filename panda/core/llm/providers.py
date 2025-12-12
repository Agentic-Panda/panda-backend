from google import genai
from google.genai import types

from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type
)

from panda.models.llm import BaseLLMClient
from panda.models.errors import LLMFailure


class GeminiClient(BaseLLMClient):
    def __init__(self, model_name: str, api_key: str, temperature: float = 0.7):
        super().__init__(model_name, temperature)

        self.client = genai.Client(api_key=api_key)
        
        self.config = types.GenerateContentConfig(
            temperature=temperature,
            candidate_count=1
        )

    @retry(
        wait=wait_random_exponential(min=5, max=60), 
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(Exception)
    )
    async def _generate_with_retry(self, prompt: str) -> str:
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=self.config
            )
            
            # safety filter returns None if triggered
            if response.text:
                return response.text.strip()
            else:
                raise Exception

        except Exception:
            raise LLMFailure

    async def generate(self, system_role: str, user_query: str) -> str:
        # TODO change to proper system prompt if needed
        full_prompt = f"System Instruction: {system_role}\n\nUser Query: {user_query}"
        return await self._generate_with_retry(full_prompt)