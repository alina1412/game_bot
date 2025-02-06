import logging

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from service.db_setup.models import (
    GameModel,
    ParticipantModel,
    QuizModel,
    UserModel,
)


@pytest.fixture(name="user_for_test1", scope="session")
async def user_for_test1(
    f_session: AsyncSession,
) -> UserModel:
    new_ = UserModel(
        id=1, first_name="user_for_test1", second_name="111", vk_id=111
    )
    f_session.add(new_)
    try:
        await f_session.commit()
    except IntegrityError:
        logging.warning("user with this id exists")
        await f_session.rollback()
    await f_session.close()


@pytest.fixture(name="fill_db_for_test", scope="session")
async def fill_db_for_test(
    user_for_test1,
    f_session: AsyncSession,
):
    models_to_add = [
        # UserModel(first_name="user_for_test2", second_name="bbb", vk_id=123),
        GameModel(chat_id=9999),
        ParticipantModel(game_id=1, user_id=1, score=0),
        QuizModel(question="qq", answer="aaa", category="common", price=200),
        QuizModel(question="qq2", answer="aaa2", category="common", price=100),
        QuizModel(question="qq3", answer="aaa3", category="common", price=200),
    ]

    for model_ in models_to_add:
        f_session.add(model_)
        await f_session.commit()

    await f_session.close()
