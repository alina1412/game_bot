from sqlalchemy import Integer, String
from sqlalchemy.orm import (
    Mapped,
    declarative_base,
    mapped_column,
)

Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    active: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="1"
    )
