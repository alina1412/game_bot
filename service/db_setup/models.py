from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from service.dataclasses import CategoryEnum


class BaseModel(DeclarativeBase):
    pass


class UserModel(BaseModel):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    second_name: Mapped[str] = mapped_column(String(50), nullable=False)
    vk_id: Mapped[int] = mapped_column(nullable=False)

    def __repr__(self):
        return "<User: {} {}>".format(self.first_name, self.second_name)


class QuizModel(BaseModel):
    __tablename__ = "quiz"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question: Mapped[str] = mapped_column(String(500), nullable=False)
    answer: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[CategoryEnum] = mapped_column(server_default="common")
    price: Mapped[int] = mapped_column(nullable=False, server_default="100")


class GameModel(BaseModel):
    __tablename__ = "game"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(nullable=False)
    finished: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=None, nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=True)
    waiting_user: Mapped[str] = mapped_column(Integer, nullable=True)


class ParticipantModel(BaseModel):
    __tablename__ = "participant"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    game_id: Mapped[int] = mapped_column(
        ForeignKey("game.id", ondelete="CASCADE")
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE")
    )
    score: Mapped[int] = mapped_column(nullable=False, server_default="0")


class RoundModel(BaseModel):
    __tablename__ = "round"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    game_id: Mapped[int] = mapped_column(
        ForeignKey("game.id", ondelete="CASCADE")
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("quiz.id", ondelete="SET NULL")
    )
    used: Mapped[str] = mapped_column(nullable=True)
    player_answers: Mapped[int] = mapped_column(nullable=True)
