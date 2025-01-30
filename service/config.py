import logging
from dataclasses import dataclass
from functools import lru_cache
from os import environ
from pathlib import Path

import yaml
from dotenv import load_dotenv

from service.bot.managers import BotManager
from service.game.accessors import (
    GameAccessor,
    GameAdminAccessor,
    UserAccessor,
)
from service.game.managers import GameManager
from service.rabbitmq_service.accessor import QueueAccessor
from service.vk_api.accessor import VkApiAccessor

# from pydantic_settings import BaseSettings

load_dotenv()

DEBUG = environ.get("DEBUG", None)

db_settings = {
    "db_name": environ.get("DB_NAME"),
    "db_host": environ.get("DB_HOST"),
    "db_user": environ.get("DB_USERNAME"),
    "db_port": environ.get("DB_PORT"),
    "db_password": environ.get("DB_PASSWORD"),
    "db_driver": environ.get("DB_DRIVER"),
}

logging.basicConfig(
    filename=("logs.log" if DEBUG else None),
    level=(logging.INFO if DEBUG else logging.WARNING),
    format=(
        "[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s"
    ),
    datefmt=("%H:%M:%S" if DEBUG else "%Y-%m-%d %H:%M:%S"),
)
logger = logging.getLogger(__name__)


class Storage:
    def __init__(self, app):
        self.user = UserAccessor(app)
        self.vk_api = VkApiAccessor(app)
        self.bots_manager = BotManager(app)
        self.game = GameAccessor(app)
        self.game_manager = GameManager(app)
        self.que = QueueAccessor(app)
        self.admin = GameAdminAccessor(app)


@dataclass
class SessionConfig:
    key: str


@dataclass
class GameConfig:
    rounds: int


@dataclass
class BotConfig:
    token: str
    group_id: int


@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"
    database: str = "project"


@dataclass
class RabbitmqConfig:
    user: str
    password: str
    host: str
    queue_title: str


@dataclass
class Config:
    session: SessionConfig | None = None
    bot: BotConfig | None = None
    database: DatabaseConfig | None = None
    game: GameConfig | None = None
    rabbit: RabbitmqConfig | None = None
    logger: logging.Logger | None = None


# class Settings(BaseSettings):
#     app_name: str = "Awesome API"
#     admin_email: str = ""
#     items_per_user: int = 50
#     storage: Storage = Storage()
#     config: Config
# settings = Settings()


def setup_config(config_path: str):
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)

    config = Config(
        session=SessionConfig(
            key=raw_config["session"]["key"],
        ),
        bot=BotConfig(
            token=raw_config["bot"]["token"],
            group_id=int(raw_config["bot"]["group_id"]),
        ),
        database=DatabaseConfig(**raw_config["database"]),
        game=GameConfig(rounds=int(raw_config["game"]["rounds"])),
        rabbit=RabbitmqConfig(**raw_config["rabbitmq"]),
        logger=logger,
    )
    return config


@lru_cache
def get_config():
    config_path = Path(__file__).parent.parent / "config.yml"
    config = setup_config(config_path)
    return config
