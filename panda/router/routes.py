from fastapi import APIRouter

from panda.core.external_api.gmail import gmail_api

router = APIRouter()


@router.get("/test")
async def test_flash():
    #await gmail_api.get_n_mails(5)


    return {"response": 'hi'}