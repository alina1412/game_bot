from fastapi import APIRouter, Depends, status

from service.config import key


api_router = APIRouter(
    prefix="/v1",
    tags=["private"],
)


@api_router.get(
    "/data1",
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Bad request"},
    },
)
async def show_data(
    # user_input: User = Depends(),
    # user_token_data=Depends(get_user_by_token)
):
    """Page"""
    return {"data": key}
