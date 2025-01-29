from dataclasses import dataclass
from enum import Enum


class CategoryEnum(Enum):
    common = "common"
    books = "books"
    tv = "tv"
    science = "science"


class GameStatusEnum(Enum):
    created_game = "created_game"
    created_rounds = "created_rounds"
    started_round_id = "started_round_id"
    player_chosing_category = "player_chosing_category"
    player_chosing_price = "player_chosing_price"
    players_think = "players_think"
    finished_round = "finished_round"
    finished = "finished"


@dataclass
class GameStatusDto:
    status: GameStatusEnum
    waiting_user: int | None


@dataclass
class PriceChoice:
    price: int
    cnt: int


@dataclass
class CategoryChoice:
    category: str
    cnt: int


@dataclass
class QuestionDto:
    question_id: int
    question: str
    round: int


@dataclass
class UserDto:
    vk_id: int
    first_name: str
    second_name: str


@dataclass
class CorrectAnswer:
    answer: str
    score: int


@dataclass
class RoundResult:
    correct_answer: str
    round_score: int


@dataclass
class Winners:
    user_id: int
    vk_id: int
    first_name: str
    second_name: str
    score: int
