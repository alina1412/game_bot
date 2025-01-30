from collections import defaultdict
from typing import TYPE_CHECKING

# from service.config import logger
from service.dataclasses import (
    CategoryChoice,
    CorrectAnswer,
    PriceChoice,
    QuestionDto,
    RoundResult,
    Winners,
)
from service.game.accessors import GameAccessor
from service.game.exceptions import GameFinishedError

if TYPE_CHECKING:
    from fastapi import FastAPI
#     from service.web.app import Application
# from app.game.accessors import GameAccessor
# from app.storage import Store


class GameManager:
    def __init__(self, app: "FastAPI") -> None:
        self.app = app
        self.rounds = app.config.game.rounds

    @property
    def logger(self):
        return self.app.config.logger

    @property
    def game_accessor(self) -> GameAccessor:
        return self.app.storage.game

    async def get_game(self, chat_id: int) -> int:
        """Game_id of current or new game"""
        was = await self.game_accessor.chat_has_running_game(chat_id)
        if was:
            return was
        return await self.generate_new_game(chat_id)

    async def generate_new_game(self, chat_id: int) -> int:
        """Return game id"""
        return await self.game_accessor.generate_new_game(chat_id)

    async def generate_rounds_for_game(
        self, game_id: int, question_amount=None
    ) -> None:
        if not question_amount:
            question_amount = self.rounds
        success = await self.game_accessor.generate_rounds_for_game(
            game_id, question_amount
        )
        if not success:
            self.logger.error(
                "rounds not generated, maybe game_id or questions[int] wrong"
            )

    async def get_next_category_choice(
        self, game_id: int
    ) -> list[CategoryChoice]:
        return await self.game_accessor.get_next_category_choice(game_id)

    async def get_next_price_choice(
        self, game_id: int, category: str
    ) -> list[PriceChoice]:
        return await self.game_accessor.get_next_price_choice(game_id, category)

    async def get_next_question(
        self, game_id: int, price: int, category: str
    ) -> QuestionDto | None:
        """Получим вопрос и отметим его waiting в раунде этой игры"""
        question_data = await self.game_accessor.get_next_question(
            game_id, price, category
        )
        if question_data:
            await self.game_accessor.mark_round_as_waiting(question_data.round)
            return question_data
        return None

    async def mark_next_answering_player(
        self, chat_id, player_vk_id
    ) -> int | None:
        return await self.game_accessor.mark_next_answering_player(
            chat_id, player_vk_id
        )

    async def player_answering_question(
        self, game_id: int, player_vk_id: int, user_answer: str
    ) -> RoundResult:
        question_id = await self.game_accessor.player_answering_question(
            game_id, player_vk_id
        )
        if not question_id:
            return False
        round_result = await self.compare_answer_to_get_score(
            question_id, user_answer
        )

        participant_id = await self.game_accessor.get_participant_id(
            player_vk_id, game_id
        )
        await self.change_participant_score(
            participant_id, round_result.round_score
        )
        return round_result

    async def compare_answer_to_get_score(
        self, question_id: int, user_answer: str
    ) -> RoundResult:
        """Ответ, количество баллов"""
        correct_answer: CorrectAnswer = (
            await self.game_accessor.get_answer_score(question_id)
        )
        if not correct_answer:
            raise NotImplementedError
        if user_answer.lower() != correct_answer.answer.lower():
            score = -correct_answer.score
        else:
            score = correct_answer.score
        return RoundResult(correct_answer.answer, score)

    async def change_participant_score(
        self, participant_id: int, add_score: int
    ) -> None:
        await self.game_accessor.change_participant_score(
            participant_id, add_score
        )

    async def get_game_winners(self, game_id: int):
        res: list[Winners] = await self.game_accessor.get_game_winners(game_id)
        if not res:
            return None
        top = defaultdict(list)
        for elem in res:
            score = elem.score
            top[score].append(elem)
        return top

    async def get_statistic_sum_score(
        self, chat_id: int, limit=100
    ) -> list[Winners]:
        return await self.game_accessor.get_statistic_sum_score(chat_id, limit)

    async def finish_game(
        self, game_id: int | None = None, chat_id: int | None = None
    ):
        await self.game_accessor.finish_game(game_id, chat_id)

    async def create_participant(self, user_id: int, game_id: int) -> None:
        if await self.game_accessor.game_is_finished(game_id):
            raise GameFinishedError
        if not await self.game_accessor.game_has_participant(user_id, game_id):
            await self.game_accessor.create_participant(user_id, game_id)

    async def amount_of_participants(self, game_id: int) -> int:
        return await self.game_accessor.amount_of_participants(game_id)
