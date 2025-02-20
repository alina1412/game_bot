from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from service.config import db_settings, logger
from service.db_setup.models import BaseModel


class DbConnector:
    def __init__(self, *args) -> None:
        self.engine: AsyncEngine | None = None
        self._db: type[DeclarativeBase] = BaseModel
        # self.session: async_sessionmaker[AsyncSession] | None = None
        self.logger = logger

    @property
    def uri(self) -> str:
        return (
            f"{db_settings['db_driver']}"
            "://"
            f"{db_settings['db_user']}:{db_settings['db_password']}"
            f"@{db_settings['db_host']}:{db_settings['db_port']}"
            f"/{db_settings['db_name']}"
        )

    def get_engine(self) -> AsyncEngine:
        self.engine = create_async_engine(
            self.uri,
            pool_size=20,
            # max_overflow=0,
            # pool_recycle=280,
            # pool_timeout=20,
            echo=True,
            future=True,
        )
        return self.engine

    @property
    def session_maker(self) -> async_sessionmaker:
        if not self.engine:
            self.get_engine()
        return async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    @property
    def session(self) -> async_sessionmaker[AsyncSession] | None:
        return self.session_maker

    async def connect(self) -> None:
        # self.session = self.session_maker()
        self.logger.info("connecting to db")
        return self.session_maker()

    async def disconnect(self) -> None:
        if self.engine:
            await self.engine.dispose()
            self.logger.info("disconnected from db")


async def get_session() -> AsyncGenerator:
    db_connector = DbConnector()
    async with db_connector.session_maker() as session:
        try:
            yield session
        except Exception as exc:
            logger.error("Error : ", exc_info=exc)
            await session.rollback()
            raise exc
        finally:
            await session.close()
            logger.info("closing db session")
            if db_connector.engine:
                await db_connector.engine.dispose()
