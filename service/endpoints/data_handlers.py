from fastapi import APIRouter, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from service.game.schemes import OkAnswerSchema, QuizSchema

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


api_router = APIRouter(
    prefix="/v1",
    tags=["private"],
)


@api_router.post(
    "/quiz-add",
    response_model=OkAnswerSchema,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Bad request"},
    },
)
async def quiz_add_handler(
    request: Request,
    Authorization: str | None = Header(default=None),
    quizzes_input: list[QuizSchema] = [],
):
    """Page add_quizzes."""
    auth = request.headers.get("Authorization")
    if not auth or auth.lower() != "bearer xxx":
        return JSONResponse(None, 401, {"WWW-Authenticate": "Basic"})
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


@api_router.get(
    "/game.statuses",
    response_model=OkAnswerSchema,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Bad request"},
    },
)
async def get_statuses_handler(
    request: Request,
):
    """Page statistics of games."""
    statistics = await request.app.storage.admin.statistic_games_status()

    return {
        "success": True,
        "data": {
            "status": 200,
            "data": {"statistics": statistics},  # settings.app_name
        },
    }


@api_router.get(
    "/user/{user_vk_id}",
    response_model=OkAnswerSchema,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Bad request"},
    },
)
async def get_user_handler(
    request: Request,
    user_vk_id: int,
):
    """Info get_user."""
    auth = request.headers.get("Authorization")
    if not auth or auth.lower() != "bearer xxx":
        return JSONResponse(None, 401, {"WWW-Authenticate": "Basic"})
    user = await request.app.storage.user.get_user(id_=None, vk_id=user_vk_id)
    return {
        "success": True,
        "data": {
            "status": 200,
            "data": user,
        },
    }
