from collections.abc import Sequence
from datetime import datetime
from typing import TYPE_CHECKING

import pytz
from sqlalchemy import Integer, Row, cast, desc, func
from sqlalchemy import insert as sa_insert
from sqlalchemy import join
from sqlalchemy import select as sa_select
from sqlalchemy import update as sa_update
from sqlalchemy.dialects.postgresql import insert as sa_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

# from service.config import logger
from service.dataclasses import (
    CategoryChoice,
    CorrectAnswer,
    GameStatusDto,
    GameStatusEnum,
    PriceChoice,
    QuestionDto,
    UserDto,
    Winners,
)
from service.db_setup.models import (
    GameModel,
    ParticipantModel,
    QuizModel,
    RoundModel,
    UserModel,
)
from service.game.schemes import StatusCountSchema, UserFoundSchema

if TYPE_CHECKING:
    from fastapi import FastAPI


class BaseAccessor:
    def __init__(self, app: "FastAPI", *args, **kwargs):
        self.app = app

    @property
    def logger(self):
        return self.app.config.logger

    @property
    async def session(
        self,
    ) -> AsyncSession:  #  -> async_sessionmaker[AsyncSession]:
        session_maker = self.app.db.session_maker
        async with session_maker() as session:
            return session

    async def get_db_result(self, query):
        async_session = await self.session
        result = await async_session.execute(query)
        await async_session.commit()
        return result


class GameAccessor(BaseAccessor):
    def __init__(self, app: "FastAPI") -> None:
        super().__init__(app)
        ...
        self.app = app

    async def get_games(self) -> GameModel | None:
        query = sa_select(GameModel).order_by(GameModel.finished.desc())
        result = await self.get_db_result(query)
        return result.scalars().all()

    async def create_participant(self, user_id: int, game_id: int) -> int:
        query = (
            sa_insert(ParticipantModel)
            .values(user_id=user_id, game_id=game_id)
            .returning(ParticipantModel.id)
        )
        result = await self.get_db_result(query)
        return result.scalar_one()

    async def amount_of_participants(self, game_id: int) -> int:
        query = (
            sa_select(func.count())
            .select_from(ParticipantModel)
            .where(ParticipantModel.game_id == game_id)
        )
        result = await self.get_db_result(query)
        return result.scalar()

    async def chat_has_running_game(self, chat_id: int) -> int | None:
        """Game_id if there's one in the chat"""
        query = sa_select(GameModel.id).where(
            GameModel.chat_id == chat_id, GameModel.finished.is_(None)
        )
        result = await self.get_db_result(query)
        return result.scalars().first()

    async def game_has_participant(self, user_id: int, game_id: int) -> bool:
        query = sa_select(ParticipantModel.user_id).where(
            ParticipantModel.user_id == user_id,
            ParticipantModel.game_id == game_id,
        )
        result = await self.get_db_result(query)
        return bool(result.scalars().first())

    async def game_is_finished(self, game_id: int) -> int | None:
        query = sa_select(GameModel.id).where(
            GameModel.id == game_id, GameModel.finished.is_not(None)
        )
        result = await self.get_db_result(query)
        return result.scalars().first()

    async def get_question(self, question_id: int) -> str:
        query = sa_select(QuizModel.question).where(QuizModel.id == question_id)
        result = await self.get_db_result(query)
        return result.scalar()

    async def generate_rounds_for_game(
        self,
        game_id: int,
        question_amount=3,
    ) -> Sequence[Row]:
        async_session = await self.session
        sub_query_choice = (
            sa_select(QuizModel.id, cast(game_id, Integer))
            .order_by(func.random())
            .limit(question_amount)
        )

        query1_insert_rounds = (
            sa_insert(RoundModel)
            .from_select(["question_id", "game_id"], sub_query_choice)
            .returning(RoundModel.id)
        )

        query2_change_status = (
            sa_update(GameModel)
            .values(status=GameStatusEnum.created_rounds.value)
            .where(GameModel.id == game_id)
        )

        result = await async_session.execute(query1_insert_rounds)
        await async_session.execute(query2_change_status)
        await async_session.commit()
        return result.all()  # [(9,), (10,), (11,)]

    async def generate_new_game(self, chat_id: int) -> int | None:
        """Return game id"""
        new_game_query1 = (
            sa_insert(GameModel).values(chat_id=chat_id).returning(GameModel.id)
        )
        status_change_query2 = sa_update(GameModel).values(
            status=GameStatusEnum.created_game.value
        )
        # TODO in one transaction
        async_session = await self.session
        result = await async_session.execute(new_game_query1)
        game_id = result.scalar_one()
        if not game_id:
            self.logger.error("not game")
            return
        status_change_query2 = status_change_query2.where(
            GameModel.id == game_id
        )
        await async_session.execute(status_change_query2)
        await async_session.commit()
        return game_id

    async def get_participant_id(self, vk_id: int, game_id: int) -> int | None:
        query = (
            sa_select(
                ParticipantModel.id,
            )
            .select_from(
                join(
                    UserModel,
                    ParticipantModel,
                    ParticipantModel.user_id == UserModel.id,
                )
            )
            .where(
                UserModel.vk_id == vk_id, ParticipantModel.game_id == game_id
            )
        )
        result = await self.get_db_result(query)
        return result.scalar()

    async def get_game_winners(self, game_id: int) -> list[Winners]:
        query = (
            sa_select(
                UserModel.id.label("user_id"),
                UserModel.vk_id,
                UserModel.first_name,
                UserModel.second_name,
                ParticipantModel.score,
            )
            .select_from(
                join(
                    UserModel,
                    ParticipantModel,
                    ParticipantModel.user_id == UserModel.id,
                )
            )
            .where(
                ParticipantModel.game_id == game_id,
                ParticipantModel.score.in_(
                    sa_select(func.distinct(ParticipantModel.score))
                    .where(ParticipantModel.game_id == game_id)
                    .order_by(ParticipantModel.score.desc())
                    .limit(3)
                ),
            )
            .order_by(ParticipantModel.score.desc())
        )
        result = await self.get_db_result(query)
        res = result.all()
        return [Winners(**elem._mapping) for elem in res]

    async def finish_game(
        self, game_id: int | None = None, chat_id: int | None = None
    ):
        if not game_id and not chat_id:
            return None

        query = sa_update(GameModel).values(
            finished=datetime.now(tz=pytz.timezone("UTC")),
            status=GameStatusEnum.finished.value,
        )
        if game_id:
            query = query.where(GameModel.id == game_id)
        if chat_id:
            query = query.where(GameModel.chat_id == chat_id)

        result = await self.get_db_result(query)
        if result.rowcount and result.returned_defaults:
            return result.returned_defaults[0]
        return None

    async def get_statistic_sum_score(
        self, chat_id: int, limit: int = 100
    ) -> list[Winners]:
        """Sum score from previous games in chat"""
        query = (
            sa_select(
                UserModel.id.label("user_id"),
                UserModel.vk_id,
                UserModel.first_name,
                UserModel.second_name,
                func.sum(ParticipantModel.score).label("score"),
            )
            .select_from(
                join(
                    UserModel,
                    ParticipantModel,
                    UserModel.id == ParticipantModel.user_id,
                ).join(
                    GameModel,
                    GameModel.id == ParticipantModel.game_id,
                )
            )
            .where(
                GameModel.chat_id == chat_id, GameModel.finished.is_not(None)
            )
            .group_by(
                UserModel.id,
                UserModel.vk_id,
                UserModel.first_name,
                UserModel.second_name,
            )
            .order_by(desc("score"))
            .limit(limit)
        )
        result = await self.get_db_result(query)
        res = result.all()
        return [Winners(**elem._mapping) for elem in res]

    async def change_participant_score(
        self, participant_id: int, add_score: int
    ):
        query = (
            sa_update(ParticipantModel)
            .values({"score": ParticipantModel.__table__.c.score + add_score})
            .where(ParticipantModel.id == participant_id)
        )
        result = await self.get_db_result(query)
        if result.rowcount and result.returned_defaults:
            return result.returned_defaults[0]
        return None

    async def get_next_price_choice(
        self, game_id: int, category: str
    ) -> list[PriceChoice]:
        query = (
            sa_select(func.count(QuizModel.id).label("cnt"), QuizModel.price)
            .select_from(
                join(
                    RoundModel,
                    QuizModel,
                    RoundModel.question_id == QuizModel.id,
                )
            )
            .where(
                RoundModel.used.is_(None),
                RoundModel.game_id == game_id,
                QuizModel.category == category,
            )
            .group_by(QuizModel.category, QuizModel.price)
            .having(func.count(QuizModel.id) > 0)
        )

        result = await self.get_db_result(query)
        return [
            PriceChoice(price=price, cnt=cnt) for cnt, price in result.all()
        ]

    async def get_next_category_choice(
        self, game_id: int
    ) -> list[CategoryChoice]:
        query = (
            sa_select(
                func.count(RoundModel.id).label("cnt"), QuizModel.category
            )
            .select_from(
                join(
                    RoundModel,
                    QuizModel,
                    RoundModel.question_id == QuizModel.id,
                )
            )
            .where(RoundModel.used.is_(None), RoundModel.game_id == game_id)
            .group_by(QuizModel.category)
            .having(func.count(RoundModel.id) > 0)
        )

        result = await self.get_db_result(query)
        return [
            CategoryChoice(category=category, cnt=cnt)
            for cnt, category in result.all()
        ]

    async def get_next_question(
        self, game_id: int, price: int, category: str
    ) -> QuestionDto | None:
        query = (
            sa_select(
                QuizModel.id.label("question_id"),
                QuizModel.question,
                RoundModel.id.label("round"),
            )
            .select_from(
                join(
                    RoundModel,
                    QuizModel,
                    RoundModel.question_id == QuizModel.id,
                )
            )
            .where(
                RoundModel.used.is_(None),
                RoundModel.game_id == game_id,
                QuizModel.price == price,
                QuizModel.category == category,
            )
        )
        result = await self.get_db_result(query)
        result = result.fetchone()
        if not result:
            return None
        return QuestionDto(**result._mapping)

    async def get_answer_score(self, question_id: int) -> CorrectAnswer:
        query = sa_select(QuizModel.answer, QuizModel.price).where(
            QuizModel.id == question_id
        )
        result = await self.get_db_result(query)
        res = result.first()
        if not res:
            raise NotImplementedError
        answer, score = res
        return CorrectAnswer(answer=answer, score=score)

    async def mark_round_as_waiting(self, round_id: int) -> None:
        query = (
            sa_update(RoundModel)
            .values(used="waiting")
            .where(RoundModel.id == round_id)
        )
        await self.get_db_result(query)

    async def mark_next_answering_player(
        self, chat_id: int, player_vk_id: int
    ) -> int | None:
        """Return RoundModel.id"""
        game_id = await self.chat_has_running_game(chat_id)
        if not game_id:
            return None
        query = (
            sa_update(RoundModel)
            .values(player_answers=player_vk_id, used="answering")
            .where(RoundModel.used == "waiting", RoundModel.game_id == game_id)
        ).returning(RoundModel.id)

        result = await self.get_db_result(query)
        return result.scalar()

    async def player_answering_question(
        self, game_id: int, player_vk_id: int
    ) -> int:
        result = await self.get_db_result(
            sa_select(RoundModel.id).where(
                RoundModel.used == "answering",
                RoundModel.game_id == game_id,
                RoundModel.player_answers == player_vk_id,
            )
            # .with_for_update(nowait=True)
        )
        round_id = result.scalar_one_or_none()
        if not round_id:
            # await session.rollback()
            return False
        return await self.use_question_in_round(None, round_id)

    async def use_question_in_round(self, session, round_id) -> int:
        query = (
            sa_update(RoundModel)
            .values(used="used")
            .where(
                RoundModel.id == round_id,
            )
            .returning(RoundModel.question_id)
        )
        result = await self.get_db_result(query)
        # await session.commit()
        self.logger.warning("round_id marked as used")
        return result.scalar()

    async def if_no_one_answers_mark_used(
        self, game_id, round_id, status="waiting"
    ):
        # TODO in one transaction
        result = await self.get_db_result(
            sa_select(RoundModel.id, RoundModel.player_answers)
            .select_from(
                join(
                    RoundModel,
                    GameModel,
                    RoundModel.game_id == GameModel.id,
                )
            )
            .where(
                RoundModel.id == round_id,
                RoundModel.used == status,
                RoundModel.game_id == game_id,
                GameModel.finished.is_(None),
            )
            # .with_for_update(nowait=True)
        )
        round_data = result.first()
        if not round_data:
            # await session.rollback()
            return None
        round_id, player_answers = round_data

        question_id = await self.use_question_in_round(None, round_id)
        correct_answer = await self.get_answer_score(question_id)
        return (correct_answer, player_answers)

    async def change_game_status(
        self, status: str, game_id: int, waiting_user: int | None = None
    ) -> None:
        vals = {"status": status, "waiting_user": waiting_user}
        query = sa_update(GameModel).values(vals).where(GameModel.id == game_id)
        await self.get_db_result(query)

    async def get_game_status(self, game_id: int) -> GameStatusDto | None:
        query = sa_select(GameModel.status, GameModel.waiting_user).where(
            GameModel.id == game_id
        )
        result = await self.get_db_result(query)
        result = result.first()
        if not result:
            return None
        status, waiting_user = result
        status = GameStatusEnum[status]
        return GameStatusDto(status, waiting_user)

    async def get_random_participants(
        self, game_id: int, limit=1
    ) -> list[UserDto]:
        query = (
            sa_select(
                UserModel.vk_id, UserModel.first_name, UserModel.second_name
            )
            .select_from(
                join(
                    UserModel,
                    ParticipantModel,
                    ParticipantModel.user_id == UserModel.id,
                )
            )
            .where(
                ParticipantModel.game_id == game_id,
            )
            .order_by(func.random())
            .limit(limit)
        )
        result = await self.get_db_result(query)
        result = result.all()
        return [UserDto(**elem._mapping) for elem in result]


class GameAdminAccessor(BaseAccessor):
    def __init__(self, app: "FastAPI") -> None:
        super().__init__(app)
        self.app = app
        ...

    async def add_quizzes(self, quizzes: list):
        if not quizzes:
            return
        new_lst = [
            {k: v for k, v in dict(quiz).items() if v is not None}
            for quiz in quizzes
        ]
        query = sa_insert(QuizModel).values(new_lst)
        await self.get_db_result(query)

    async def statistic_games_status(self) -> list[StatusCountSchema]:
        query = (
            sa_select(GameModel.status, func.count().label("count"))
            .select_from(GameModel)
            .group_by(GameModel.status)
            .order_by(GameModel.status)
        )
        result = (await self.get_db_result(query)).fetchall()
        return [StatusCountSchema(**elem._mapping) for elem in result]


class UserAccessor(BaseAccessor):
    def __init__(self, app: "FastAPI") -> None:
        super().__init__(app)
        self.config = app.config
        self.app = app

    async def get_user(
        self, id_: int | None, vk_id: int | None
    ) -> UserFoundSchema | None:
        if not id_ and not vk_id:
            return None
        query = sa_select(UserModel)
        query = (
            query.where(UserModel.id == id_)
            if id_
            else query.where(UserModel.vk_id == vk_id)
        )

        result = await self.get_db_result(query)
        user = result.scalars().first()
        if not user:
            return None
        return UserFoundSchema(
            **{
                "vk_id": user.vk_id,
                "first_name": user.first_name,
                "second_name": user.second_name,
            }
        )

    async def create_user_if_not_exists(self, user: UserDto) -> int:
        # TODO
        async_session = await self.session
        select_user_id_result = await async_session.execute(
            sa_select(UserModel.id).where(UserModel.vk_id == user.vk_id)
            # .with_for_update()
        )
        user_id = select_user_id_result.scalar_one_or_none()
        if user_id:
            await async_session.rollback()
        else:
            insert_user_query = (
                sa_insert(UserModel)
                .values(
                    vk_id=user.vk_id,
                    first_name=user.first_name,
                    second_name=user.second_name,
                )
                .returning(UserModel.id)
            )
            select_user_id_result = await async_session.execute(
                insert_user_query
            )
            await async_session.commit()
            user_id = select_user_id_result.scalars().first()
        return user_id
