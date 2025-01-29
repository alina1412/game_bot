from fastapi import APIRouter, Depends, status


api_router = APIRouter(
    prefix="/v1",
    tags=["private"],
)


@api_router.post(
    "/data",
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Bad request"},
    },
)
async def post_data():
    """"""
    return {"data": "user_token_data"}
