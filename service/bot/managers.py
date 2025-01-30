import asyncio
import json
import random
import typing
from logging import getLogger

from service.bot.dataclasses import CatRoundParams, EventTypes
from service.bot.utils import CATEGORY_NAMES
from service.dataclasses import (
    CategoryChoice,
    GameStatusEnum,
    RoundResult,
    UserDto,
    Winners,
)
from service.game.exceptions import GameFinishedError
from service.game.managers import GameManager
from service.vk_api.btn_creator import BtnCreator
from service.vk_api.dataclasses import BtnData, ChatInvite, Message, Update

if typing.TYPE_CHECKING:
    from fastapi import FastAPI

    # from service.web.app import Application


class CatGameEventsBotManager:
    def __init__(self, app: "FastAPI"):
        self.app = app

    @property
    def bot_manager(self):
        return self.app.storage.bots_manager

    @property
    def game_manager(self) -> GameManager:
        return self.app.storage.game_manager

    async def cat_receiver(self, message: Update):
        chat_id = message.object.message.peer_id
        user_vk_id = message.object.message.payload.get("vk_id")
        question_id = message.object.message.payload.get("question_id")
        round_id = message.object.message.payload.get("round_id")

        from_id = message.object.message.payload.get("from_id")
        if not from_id or not question_id:
            await self.bot_manager.reaction_on_wrong_text(message)
            return
        if from_id != message.object.message.from_id:
            return

        member = (
            await self.bot_manager.round_manager.get_user_and_mark_to_answer(
                message, user_vk_id, round_id
            )
        )
        if not member:
            await self.bot_manager.reaction_on_wrong_text(message)
            return

        question = await self.app.storage.game.get_question(question_id)
        text = question + (
            "\nОтвечает: "
            + self.bot_manager.get_user_mention(member)
            + ". "
            + "Введите ответ текстом."
        )
        new_message = self.bot_manager.get_message(text, chat_id)
        await self.app.storage.vk_api.send_message(new_message, keyboard=[])

    async def parse_cat_params(self, message: Update, params: CatRoundParams):
        for attr in ("from_id", "round_id", "question_id"):
            if not getattr(params, attr):
                setattr(params, attr, message.object.message.payload.get(attr))
        return params

    def get_cat_keyboard(
        self, game_id: int, chat_members: list[UserDto], params: CatRoundParams
    ):
        lst_of_btns = [
            BtnData(
                label=f"{member.first_name} {member.second_name}"[:40],
                payload=json.dumps(
                    {
                        "btn": EventTypes.cat_receiver,
                        "vk_id": member.vk_id,
                        "question_id": params.question_id,
                        "from_id": params.from_id,
                        "game_id": game_id,
                        "round_id": params.round_id,
                    }
                ),
            )
            for member in chat_members[: max(0, params.limit - 1)]
        ]
        if len(chat_members) > params.limit - 1:
            lst_of_btns.append(
                BtnData(
                    label="показать ещё",
                    payload=json.dumps(
                        {
                            "btn": EventTypes.cat_in_bag,
                            "question_id": params.question_id,
                            "from_id": params.from_id,
                            "game_id": game_id,
                            "round_id": params.round_id,
                        }
                    ),
                ),
            )
        return BtnCreator().get_not_inline_callback_keyboard(lst_of_btns)

    async def suggest_random_members(
        self, message: Update, params: CatRoundParams
    ) -> None:
        params = await self.parse_cat_params(message, params)
        if params.from_id != message.object.message.from_id:
            return
        if not params.question_id and params.round_id:
            await self.bot_manager.reaction_on_wrong_text(message)
            return
        chat_id = message.object.message.peer_id
        game_id = message.object.message.payload.get("game_id")

        await self.app.storage.game.change_game_status(
            GameStatusEnum.players_think.value, game_id, waiting_user=None
        )
        chat_members = await self.app.storage.vk_api.get_conversation_members(
            chat_id
        )
        if not chat_members:
            await self.bot_manager.reaction_on_wrong_text(message)
            return
        random.shuffle(chat_members)

        text = "\n".join(  # noqa: FLY002
            (
                params.text,
                "Кот в мешке! Выберите, кому отдать вопрос (можно себе)",
            )
        )
        keyboard = self.get_cat_keyboard(game_id, chat_members, params)
        new_message = self.bot_manager.get_message(text, chat_id)
        await self.app.storage.vk_api.send_message(
            new_message, keyboard=keyboard
        )


class GamePreparationBotManager:
    def __init__(self, app: "FastAPI"):
        self.app = app

    @property
    def bot_manager(self):
        return self.app.storage.bots_manager

    @property
    def game_manager(self) -> GameManager:
        return self.app.storage.game_manager

    async def suggest_to_start_game(
        self, chat_id: int, game_id: int, chat_members: list[UserDto]
    ):
        if not chat_members:
            return
        if len(chat_members) < 2:
            text = "В чате для игры должно быть хотя бы 2 участника \
                (не включая бота). Для начала игры напишите \
                команду /start."
        else:
            lst_names = [
                self.bot_manager.get_user_mention(member)
                for member in chat_members
            ]
            list_category_choice = (
                await self.bot_manager.game_manager.get_next_category_choice(
                    game_id
                )
            )

            intro = (
                "\nВ игре будут следующие категории: "
                + ", ".join(
                    [
                        CATEGORY_NAMES[category.category.value]
                        for category in list_category_choice
                    ]
                )
                + "\nВсего вопросов: {}.\n".format(
                    sum([category.cnt for category in list_category_choice])  # noqa: C419
                )
            )

            text = (
                "☀ Мы можем провести викторину Своя игра!\
                    Напомню, так же всегда доступны команды /start и /stop.\
                    Нажимайте на кнопки и отвечайте на вопросы. \
                    Проверьте перечисленных участников:\n"
                + "\n".join(lst_names)
            ) + intro
        lst_of_btns = [
            BtnData(
                label="Посмотреть статистику?",
                payload=json.dumps({"btn": EventTypes.show_stat}),
            ),
            BtnData(
                label="Обновить участников?",
                payload=json.dumps(
                    {"btn": EventTypes.renew_players, "game_id": game_id}
                ),
            ),
        ]
        if len(chat_members) > 1:
            lst_of_btns.append(
                BtnData(
                    label="Начать игру?",
                    payload=json.dumps(
                        {"btn": EventTypes.start_round, "game_id": game_id}
                    ),
                ),
            )
        keyboard = BtnCreator().get_not_inline_callback_keyboard(lst_of_btns)
        new_message = self.bot_manager.get_message(text, chat_id)
        await self.app.storage.vk_api.send_message(
            new_message, keyboard=keyboard
        )

    async def generate_game_and_send_message(self, chat_id: int):
        game_id = await self.app.storage.game.chat_has_running_game(chat_id)
        if not game_id:
            game_id = await self.generate_game_and_rounds(chat_id)
        chat_members = await self.app.storage.vk_api.get_conversation_members(
            chat_id
        )
        await self.suggest_to_start_game(chat_id, game_id, chat_members)
        await self.create_users_and_participants(game_id, chat_members)

    async def generate_game_and_rounds(self, chat_id: int) -> int:
        game_id = await self.bot_manager.game_manager.generate_new_game(chat_id)
        await self.bot_manager.game_manager.generate_rounds_for_game(game_id)
        return game_id

    async def create_users_and_participants(
        self, game_id: int, chat_members: list[UserDto]
    ):
        for user in chat_members:
            user_id = await self.app.storage.user.create_user_if_not_exists(
                user
            )
            try:
                await self.game_manager.create_participant(user_id, game_id)
            except GameFinishedError:
                return

    async def reaction_on_btn_renew_players(self, message: Update):
        chat_id = message.object.message.peer_id
        game_id = message.object.message.payload.get("game_id")
        chat_members = await self.app.storage.vk_api.get_conversation_members(
            chat_id
        )
        await self.suggest_to_start_game(chat_id, game_id, chat_members)
        await self.create_users_and_participants(game_id, chat_members)

    async def add_late_user_to_game(self, chat_id: int, member_id: int):
        game_id = await self.game_manager.get_game(chat_id)
        if not game_id:
            return
        add_user = await self.app.storage.vk_api.get_user_info(member_id)
        await self.create_users_and_participants(game_id, [add_user])

    async def prepare_to_repeat_game(self, message: Update, short=False):
        chat_id = message.object.message.peer_id
        game_id = await self.generate_game_and_rounds(chat_id)
        chat_members = await self.app.storage.vk_api.get_conversation_members(
            chat_id
        )
        await self.create_users_and_participants(game_id, chat_members)
        if not short:
            await self.suggest_to_start_game(chat_id, game_id, chat_members)
        else:
            new_message = self.bot_manager.get_message("Сыграть ещё?", chat_id)
            await self.bot_manager.send_continue_btn(chat_id, new_message)


class GameRoundBotManager:
    def __init__(self, app: "FastAPI"):
        self.app = app

    @property
    def bot_manager(self):
        return self.app.storage.bots_manager

    @property
    def game_manager(self) -> GameManager:
        return self.app.storage.game_manager

    async def choose_user_for_action(
        self,
        message: Update,
        game_id: int,
        round_result: RoundResult | None = None,
        player_vk_id: int | None = None,
    ) -> UserDto:
        if round_result and round_result.round_score > 0:
            user = await self.app.storage.user.get_user(
                id_=None, vk_id=player_vk_id
            )
            return UserDto(**user)

        users = await self.app.storage.game.get_random_participants(
            game_id, limit=2
        )
        if not users:
            await self.bot_manager.reaction_on_wrong_text(
                message, "участники не найдены..."
            )
        if users[0].vk_id == player_vk_id and len(users) > 1:
            return users[1]
        return users[0]

    async def reaction_on_chosing_btns(self, message: Update):
        event_type = message.object.message.payload.get("btn")
        game_id = message.object.message.payload.get("game_id")
        game_status = await self.app.storage.game.get_game_status(game_id)
        if game_status.waiting_user != message.object.message.from_id:
            return

        if event_type == EventTypes.choose_category:
            await self.message_for_round_choose_price(message)

        elif event_type == EventTypes.choose_price:
            await self.send_quiz_question(message)

    async def message_for_round_choose_category(
        self,
        message: Update,
        game_id: int,
        player_vk_id: int,
        list_category_choice: list[CategoryChoice],
        round_result: RoundResult | None = None,
    ):
        """Предложить выбрать категорию (или автоматом через 20 сек?)"""
        chat_id = message.object.message.peer_id
        lst_of_btns = [
            BtnData(
                label=(
                    f"{CATEGORY_NAMES[category_choice.category.name]}"
                    f" ({category_choice.cnt} шт.)"
                ),
                payload=json.dumps(
                    {
                        "btn": EventTypes.choose_category,
                        "game_id": game_id,
                        "category": category_choice.category.value,
                    }
                ),
            )
            for category_choice in list_category_choice
        ]
        keyboard = BtnCreator().get_not_inline_callback_keyboard(
            lst_of_btns, one_time=False
        )

        user = await self.choose_user_for_action(
            message, game_id, round_result, player_vk_id
        )

        text = (
            f"Ход: {self.bot_manager.get_user_mention(user)}. "
            "Выберите категорию."
        )
        new_message = self.bot_manager.get_message(text, chat_id)
        await self.app.storage.vk_api.send_message(
            new_message, keyboard=keyboard
        )

        await self.app.storage.game.change_game_status(
            GameStatusEnum.player_chosing_category.value,
            game_id,
            waiting_user=user.vk_id,
        )

    async def message_for_round_choose_price(self, message: Update):
        """Предложить выбрать цену (или автоматом через 20 сек?)"""
        chat_id = message.object.message.peer_id
        game_id = message.object.message.payload.get("game_id")
        category = message.object.message.payload.get("category")
        list_price_choice = await self.game_manager.get_next_price_choice(
            game_id, category
        )
        if not list_price_choice:
            await self.bot_manager.reaction_on_wrong_text(message)
            return

        lst_of_btns = [
            BtnData(
                label=(f"{price_choice.price} ({price_choice.cnt} шт.)"),
                payload=json.dumps(
                    {
                        "btn": EventTypes.choose_price,
                        "game_id": game_id,
                        "category": category,
                        "price": price_choice.price,
                    }
                ),
            )
            for price_choice in list_price_choice
        ]
        keyboard = BtnCreator().get_not_inline_callback_keyboard(
            lst_of_btns, one_time=False
        )
        status = await self.app.storage.game.get_game_status(game_id)
        if not status.waiting_user:
            self.logger.error("no user in status")
            await self.bot_manager.reaction_on_wrong_text("something wrong")
            return
        user = await self.app.storage.vk_api.get_user_info(status.waiting_user)

        text = (
            f"Выбрана категория: {CATEGORY_NAMES[category]}.\n"
            f"Ход: {self.bot_manager.get_user_mention(user)}."
            " Выберите цену вопроса."
        )

        new_message = self.bot_manager.get_message(text, chat_id)
        await self.app.storage.vk_api.send_message(
            new_message, keyboard=keyboard
        )
        await self.app.storage.game.change_game_status(
            GameStatusEnum.player_chosing_price.value,
            game_id,
            waiting_user=user.vk_id,
        )

    async def time_limit_waiting_msg(self, message: Update, game_id, round_id):
        """Если все еще раунд waiting, послать кнопку пропуска"""
        await asyncio.sleep(10)
        data_status = await self.app.storage.game.if_no_one_answers_mark_used(
            game_id, round_id, "waiting"
        )
        if not data_status:
            return
        answer, _ = data_status

        lst_of_btns = [
            BtnData(
                label="Пропуск",
                payload=json.dumps(
                    {
                        "btn": EventTypes.start_round,
                        "game_id": game_id,
                    }
                ),
            )
        ]
        keyboard = BtnCreator().get_not_inline_callback_keyboard(
            lst_of_btns, one_time=False
        )
        text = f"""Время вышло. Правильный ответ {answer.answer}"""
        new_message = self.bot_manager.get_message(
            text, message.object.message.peer_id
        )
        await self.app.storage.vk_api.send_message(
            new_message, keyboard=keyboard
        )

    async def time_limit_answering_msg(
        self, message: Update, game_id, round_id
    ):
        """Если все еще раунд answering, послать кнопку пропуска"""
        await asyncio.sleep(10)
        data_status = await self.app.storage.game.if_no_one_answers_mark_used(
            game_id, round_id, "answering"
        )
        if not data_status:
            return
        answer, user_vk_id = data_status

        score = answer.score
        user = await self.app.storage.user.get_user(id_=None, vk_id=user_vk_id)
        user_mention = self.bot_manager.get_user_mention(UserDto(**user))

        lst_of_btns = [
            BtnData(
                label="Дальше",
                payload=json.dumps(
                    {
                        "btn": EventTypes.start_round,
                        "game_id": game_id,
                    }
                ),
            )
        ]
        keyboard = BtnCreator().get_not_inline_callback_keyboard(
            lst_of_btns, one_time=False
        )
        text = f"{user_mention}, время вышло. Правильный ответ {answer.answer}\
            -{score} балл(ов)"
        new_message = self.bot_manager.get_message(
            text, message.object.message.peer_id
        )
        await self.app.storage.vk_api.send_message(
            new_message, keyboard=keyboard
        )

        participant_id = await self.app.storage.game.get_participant_id(
            user_vk_id, game_id
        )
        await self.game_manager.change_participant_score(
            participant_id, add_score=-score
        )

    async def send_quiz_question(self, message: Update):
        game_id = message.object.message.payload.get("game_id")
        category = message.object.message.payload.get("category")
        price = message.object.message.payload.get("price")
        question = await self.game_manager.get_next_question(
            game_id=game_id, price=price, category=category
        )
        round_id = question.round
        attachment = None
        if "photo" in question.question:
            attachment = question.question
            question.question = "Что изображено на картинке?"
        elif "кот в мешке" in question.question:
            await self.bot_manager.cat_in_box_manager.suggest_random_members(
                message,
                CatRoundParams(
                    question_id=question.question_id,
                    text=f"Выбрана цена вопроса: {price}.\n",
                    from_id=message.object.message.from_id,
                    round_id=round_id,
                ),
            )
            return

        lst_of_btns = [
            BtnData(
                label="Готов Ответить",
                payload=json.dumps(
                    {
                        "btn": EventTypes.ready,
                        "game_id": game_id,
                        "question_id": question.question_id,
                        "round_id": round_id,
                    }
                ),
            )
        ]
        keyboard = BtnCreator().get_not_inline_callback_keyboard(
            lst_of_btns, one_time=False
        )
        text = f"""Выбрана цена вопроса: {price}.\n
                Вопрос:  {question.question}. \n
                Отвечает игрок, нажавший первым кнопку 'Готов Ответить'"""
        new_message = self.bot_manager.get_message(
            text, message.object.message.peer_id
        )
        await self.app.storage.vk_api.send_message(
            new_message, keyboard=keyboard, photo_id=attachment
        )
        await self.app.storage.game.change_game_status(
            GameStatusEnum.players_think.value, game_id, waiting_user=None
        )

        self.wait_task = asyncio.create_task(
            self.time_limit_waiting_msg(message, game_id, question.round)
        )
        self.wait_task.add_done_callback(self._done_callback)

    async def get_user_and_mark_to_answer(
        self, message: Update, user_vk_id, round_id
    ) -> UserDto:
        chat_id = message.object.message.peer_id
        affected = await self.game_manager.mark_next_answering_player(
            chat_id, user_vk_id
        )
        if not affected:
            return None
        game_id = await self.app.storage.game.chat_has_running_game(chat_id)
        self.ans_wait_task = asyncio.create_task(
            self.time_limit_answering_msg(message, game_id, round_id)
        )
        self.ans_wait_task.add_done_callback(self._done_callback)
        return await self.app.storage.vk_api.get_user_info(user_vk_id)

    async def reaction_on_ready_to_answer(self, message: Update):
        user_vk_id = message.object.message.from_id
        round_id = message.object.message.payload.get("round_id")
        member = await self.get_user_and_mark_to_answer(
            message, user_vk_id, round_id
        )
        if not member:
            return

        text = (
            "Готов(а) ответить "
            + self.bot_manager.get_user_mention(member)
            + ". "
            + "Введите ответ текстом."
        )
        new_message = self.bot_manager.get_message(
            text, message.object.message.peer_id
        )
        await self.app.storage.vk_api.send_message(new_message, keyboard=[])

    async def reaction_on_answer_question(self, message: Update):
        user_answer = message.object.message.text
        chat_id = message.object.message.peer_id
        player_vk_id = message.object.message.from_id

        game_id = await self.app.storage.game.chat_has_running_game(chat_id)
        if not game_id:
            await self.bot_manager.reaction_on_wrong_text(
                message,
                """ возможно, игра не начата\n напишите команду /start""",
            )
            return

        round_result = await self.game_manager.player_answering_question(
            game_id, player_vk_id, user_answer
        )

        if not round_result:
            # await self.bot_manager.reaction_on_wrong_text(message)
            return
        text_is_correct = "Правильно!\n" if round_result.round_score > 0 else ""
        text = (
            text_is_correct
            + f"""Правильный ответ: {round_result.correct_answer}\n
            Баллы за раунд: {round_result.round_score}.
            """
        )
        new_message = self.bot_manager.get_message(
            text, message.object.message.peer_id
        )
        await self.app.storage.vk_api.send_message(new_message)
        await self.reaction_next_step_or_end(
            message, game_id, round_result, player_vk_id
        )

    async def reaction_next_step_or_end(
        self,
        message: Update,
        game_id=None,
        round_result: RoundResult | None = None,
        player_vk_id: int | None = None,
    ):
        """Выбор новой категории для следующего вопроса
        или вопросы закончились
        """
        if not game_id:
            game_id = message.object.message.payload.get("game_id")
        if not player_vk_id:
            player_vk_id = message.object.message.from_id
        list_category_choice = await self.game_manager.get_next_category_choice(
            game_id
        )
        if not list_category_choice:
            await self.game_manager.finish_game(game_id)
            success = await self.bot_manager.message_for_winners_end(
                message, game_id
            )
            short = bool(success)
            await self.bot_manager.preparation_manager.prepare_to_repeat_game(
                message, short
            )
            return
        await self.message_for_round_choose_category(
            message, game_id, player_vk_id, list_category_choice, round_result
        )

    def _done_callback(self, result: asyncio.Future) -> None:
        if result.exception():
            self.logger.exception(
                "task stopped with exception", exc_info=result.exception()
            )


class BotManager:
    def __init__(self, app: "FastAPI"):
        self.app = app
        self.bot = None
        self.logger = getLogger("handler")
        self.cat_in_box_manager = CatGameEventsBotManager(app)
        # self.statistic_manager = ChatStatisticBotManager(app)
        self.preparation_manager = GamePreparationBotManager(app)
        self.round_manager = GameRoundBotManager(app)

    @property
    def game_manager(self) -> GameManager:
        return self.app.storage.game_manager

    def is_member_a_game_bot(self, member_id: int) -> bool:
        return member_id == -self.app.config.bot.group_id

    async def handle_updates(self, update: dict):
        if not update:
            return
        if update["type"] == "message_event":
            update = Update.from_dict(update)
            await self.process_event(update)
        elif update["type"] == "chat_invite_user":
            update = ChatInvite.from_dict(update)
            await self.process_chat_invite_event(update)
        elif update["type"] == "message_new":
            update = Update.from_dict(update)
            await self.handle_message_new_type_updates(update)

    async def handle_message_new_type_updates(self, update: Update):
        if update.object.message.text == "/start":
            await self.reaction_on_start_command(update)
        elif update.object.message.text == "/stop":
            await self.reaction_on_stop_command(update)
        else:
            await self.round_manager.reaction_on_answer_question(update)

    async def reaction_on_start_command(self, update: Update):
        peer_id = update.object.message.peer_id
        await self.stop_all_games_in_chat(peer_id)
        await self.preparation_manager.generate_game_and_send_message(peer_id)

    async def reaction_on_stop_command(self, update: Update):
        chat_id = update.object.message.peer_id
        game_id = await self.app.storage.game.chat_has_running_game(chat_id)
        success = False
        if game_id:
            success = await self.message_for_winners_end(update, game_id)
            await self.stop_all_games_in_chat(chat_id)
        short = bool(success)
        await self.preparation_manager.prepare_to_repeat_game(
            update, short=short
        )

    async def stop_all_games_in_chat(self, chat_id: int) -> None:
        await self.game_manager.finish_game(chat_id=chat_id)

    async def send_bot_joins_chat_message(self, chat_id: int) -> None:
        text = "Я бот по проведению викторины Своя игра в беседе. \
        Назначьте меня админом и запустите игру, написав /start. \
        Нажимайте на кнопки и отвечайте на вопросы. Для досрочной \
        остановки команда: /stop"
        new_message = self.get_message(text, chat_id)
        await self.app.storage.vk_api.send_message(new_message)

    async def process_chat_invite_event(self, message: ChatInvite):
        chat_id = message.peer_id
        if self.is_member_a_game_bot(message.member_id):
            await self.send_bot_joins_chat_message(chat_id)
        elif message.member_id > 0:
            await self.preparation_manager.add_late_user_to_game(
                chat_id, message.member_id
            )

    def get_user_mention(self, user: UserDto | Winners) -> str:
        return f"[id{user.vk_id}|{user.first_name} {user.second_name}]"

    def get_message(self, text: str, chat_id: int) -> Message:
        return Message(
            user_id=None,
            text=text,
            peer_id=chat_id,
        )

    async def message_for_winners_end(
        self, message: Update, game_id: int
    ) -> bool:
        winners = await self.game_manager.get_game_winners(game_id)
        if not winners:
            return False
        plases = ("Первое место: ", "\nВторое место: ", "\nТретье место: ")
        data = ["Игра закончена!\n"]
        for i, score_ in enumerate(winners):
            text_won = plases[i]
            data.extend([text_won, str(score_) + " балл(ов) "])
            for member in winners[score_]:
                data.append(  # noqa: PERF401
                    self.get_user_mention(member) + "\n"
                )
        text = "".join(data)
        new_message = self.get_message(text, message.object.message.peer_id)
        await self.app.storage.vk_api.send_message(new_message)
        return True

    async def show_statistics_of_chat(self, message: Update):
        chat_id = message.object.message.peer_id
        statistic = await self.app.storage.game.get_statistic_sum_score(chat_id)
        if not statistic:
            data_to_show = ["Возможно, ещё не было игр"]
        else:
            data_to_show = ["Баллы суммарно по всем играм в чате"]
        for winner in statistic:
            data_to_show.append(
                f"{winner.score} б.: " + self.get_user_mention(winner)
            )
        text = "\n".join(data_to_show)
        new_message = self.get_message(text, chat_id)
        await self.send_continue_btn(chat_id, new_message)

    async def reaction_on_wrong_text(
        self, message: Update, text: str | None = ""
    ):
        text = (
            """что-то пошло не так..
            """
            + text
        )
        new_message = self.get_message(text, message.object.message.peer_id)
        await self.app.storage.vk_api.send_message(new_message)

    async def send_continue_btn(self, chat_id: int, text: str):
        if not text:
            self.logger.error("no text")
            return
        game_id = await self.game_manager.get_game(chat_id)
        lst_of_btns = [
            BtnData(
                label="Продолжить",
                payload=json.dumps(
                    {"btn": EventTypes.renew_players, "game_id": game_id}
                ),
            ),
        ]
        keyboard = BtnCreator().get_not_inline_callback_keyboard(lst_of_btns)
        await self.app.storage.vk_api.send_message(text, keyboard=keyboard)

    async def process_event(self, message: Update):
        """Callback on button"""
        event_type = message.object.message.payload.get("btn")
        if event_type == EventTypes.start_round:
            await self.round_manager.reaction_next_step_or_end(message)

        elif event_type in (
            EventTypes.choose_category,
            EventTypes.choose_price,
        ):
            await self.round_manager.reaction_on_chosing_btns(message)

        elif event_type == EventTypes.ready:
            await self.round_manager.reaction_on_ready_to_answer(message)
        elif event_type == EventTypes.renew_players:
            await self.preparation_manager.reaction_on_btn_renew_players(
                message
            )
        elif event_type == EventTypes.show_stat:
            await self.show_statistics_of_chat(message)
        elif event_type == EventTypes.cat_in_bag:
            await self.cat_in_box_manager.suggest_random_members(
                message, CatRoundParams()
            )
        elif event_type == EventTypes.cat_receiver:
            await self.cat_in_box_manager.cat_receiver(message)
        await self.app.storage.vk_api.sent_answer_to_event(message)
