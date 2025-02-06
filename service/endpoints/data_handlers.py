from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from service.game.schemes import OkAnswerSchema, QuizSchema, QuizzesListSchema

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


from service.config import DEBUG  # , get_settings, Settings
from service.db_setup.db_connector import get_session

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
async def quiz_add_handler(
    # user_input: User = Depends(),
    # user_token_data=Depends(get_user_by_token)
    # token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    # session: AsyncSession = Depends(get_session),
    Authorization: str | None = Header(default=None),
    quizzes_input: list[QuizSchema] = [],
):
    """Page add_quizzes"""
    """auth = request.headers.get("Authorization")
    if not auth or auth.lower() != "bearer kts":
        raise HTTPUnauthorized"""
    if not quizzes_input:
        raise HTTPException(status_code=400, detail="No data provided to add")
    try:
        await request.app.storage.admin.add_quizzes(quizzes_input)
    except IntegrityError as exc:
        request.app.db.logger.error("error: ", exc_info=exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
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
    """Page statistics of games"""
    statistics = await request.app.storage.admin.statistic_games_status()

    return {
        "success": True,
        "data": {
            "status": 200,
            "data": {"statistics": statistics},  # settings.app_name
        },
    }


# UserSearchView
@api_router.get(
    "/user/{user_vk_id}",
    response_model=OkAnswerSchema,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Bad request"},
    },
)
async def get_user(
    request: Request,
    user_vk_id: int,
    # user_input: User = Depends(),
    # user_token_data=Depends(get_user_by_token)
):
    """Info get_user"""
    user = await request.app.storage.user.get_user(id_=None, vk_id=user_vk_id)
    return {
        "success": True,
        "data": {
            "status": 200,
            "data": user,
        },
    }
