from fastapi import APIRouter

#from panda.core.workflow.manual_flow import run_workflow
from panda.core.external_api.gmail import gmail_api

router = APIRouter()


@router.get("/test")
async def test_flash():
    #await run_workflow("Create a draft email about the topic LLM. keep the email short")
    #await gmail_api.get_n_mails(5)

    await gmail_api.draft_email('vinayakmundakkal@protonmail.com', 'Test', 'This a test message')

    return {"response": 'hi'}