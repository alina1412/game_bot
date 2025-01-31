from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from service.db_setup.db_connector import get_session

api_router = APIRouter(
    prefix="/v1",
    tags=["private"],
)


@api_router.put(
    "/data2",
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Bad request"},
    },
)
async def put_data2(
    add_data=None, session: AsyncSession = Depends(get_session)
):
    """example with postgres sqlalchemy"""

    return {"user_id": 1}
