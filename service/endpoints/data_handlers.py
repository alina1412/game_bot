from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

# from service.__main__ import get_settings
from service.game.schemes import OkAnswerSchema, QuizzesListSchema

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


from service.config import DEBUG  # , get_settings, Settings
from service.db_setup.db_settings import get_session

api_router = APIRouter(
    prefix="/v1",
    tags=["private"],
)


# QuizAddView
@api_router.post(
    "/quiz-add",
    response_model=OkAnswerSchema,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Bad request"},
    },
)
async def quiz_add(
    # user_input: User = Depends(),
    # user_token_data=Depends(get_user_by_token)
    # token: Annotated[str, Depends(oauth2_scheme)],
    session: AsyncSession = Depends(get_session),
    Authorization: str | None = Header(default=None),
    quizzes: QuizzesListSchema = [],
):
    """Page"""
    """auth = request.headers.get("Authorization")
    if not auth or auth.lower() != "bearer kts":
        raise HTTPUnauthorized"""
    return {
        "success": True,
        "data": {
            "status": 200,
            "data": {},
        },
    }


# StatusCountView
@api_router.get(
    "/game.statuses",
    response_model=OkAnswerSchema,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Bad request"},
    },
)
async def get_status_count(
    request: Request,
    # user_input: User = Depends(),
    # user_token_data=Depends(get_user_by_token)
    # settings: Settings = Depends(get_settings),
):
    """Page"""
    # assert settings.config.database.database

    assert request.app.config.game

    return {
        "success": True,
        "data": {
            "status": 200,
            "data": {"s": True},  # settings.app_name
        },
    }


# UserSearchView
@api_router.get(
    "/get-user",
    response_model=OkAnswerSchema,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Bad request"},
    },
)
async def get_user(
    # user_input: User = Depends(),
    # user_token_data=Depends(get_user_by_token)
):
    """Page"""
    return {
        "success": True,
        "data": {
            "status": 200,
            "data": {},
        },
    }
