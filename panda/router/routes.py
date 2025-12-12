from fastapi import APIRouter

from ..core.llm.factory import LLMProvider, LLMFactory
from panda import Config


router = APIRouter()

# TODO change response model
@router.get("/testmodelflash")
async def test_flash():
    ai = LLMFactory.create_client(LLMProvider.GEMINI, api_key=Config.GEMINI_API, model_name='gemini-2.5-flash')

    response = await ai.generate(
        system_role='Robot',
        user_query='Who are you?'
    )

    return {"response": response}