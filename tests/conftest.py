import warnings
from collections.abc import Iterator
from typing import Any, AsyncGenerator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from service.db_setup.models import BaseModel

warnings.filterwarnings("ignore", category=DeprecationWarning)


from service.__main__ import app
from service.db_setup.db_connector import DbConnector

from .fixtures import *


@pytest_asyncio.fixture(name="f_session", scope="session")
async def get_test_session() -> AsyncGenerator[sessionmaker, None]:
    async with DbConnector().session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            await session.close()


@pytest.fixture(name="cli", scope="session")
def fixture_client() -> TestClient:  # type: ignore
    with TestClient(app) as client:
        yield client


@pytest.fixture(name="clear_db", autouse=False)
async def clear_db() -> Iterator[None]:
    try:
        yield
    except Exception as err:
        logging.warning(err)
    finally:
        async with DbConnector().session_maker() as session:
            try:
                connection = await session.connection()
                target_metadata = BaseModel.metadata
                for table in target_metadata.tables:
                    table_exists = (
                        await connection.execute(
                            text(
                                f"SELECT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = '{table}')"
                            )
                        )
                    ).fetchone()[0]

                    if table_exists:
                        await connection.execute(
                            text(f"""TRUNCATE "{table}" CASCADE;""")
                        )
                        await connection.execute(
                            text(
                                f"ALTER SEQUENCE {table}_id_seq RESTART WITH 1;"
                            )
                        )
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()
