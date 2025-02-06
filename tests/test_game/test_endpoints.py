import logging

# from urllib.parse import urlencode
import pytest
from fastapi.testclient import TestClient

from service.db_setup.models import (
    GameModel,
    ParticipantModel,
    QuizModel,
    UserModel,
)

pytest_plugins = ("pytest_asyncio",)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

pytestmark = pytest.mark.asyncio


class TestHandlersView:
    async def test_statuses(
        self,
        cli: TestClient,
        user_for_test1,  # fixture add user
        fill_db_for_test,
        clear_db,  # если очистить базу после теста
    ) -> None:
        """Тестирует ручку /game.statuses с предварительным заполнением базы"""
        response = cli.get(
            "/v1/game.statuses",
            headers={"Authorization": "xxx"},
        )
        assert response.status_code == 200
        data = response.json()
        logger.info(data)

    async def test_admin_get_user(
        self,
        cli: TestClient,
        user_for_test1,  # fixture add user
        clear_db,  # если очистить базу после теста
    ) -> None:
        """Тестирует ручку /user с предварительным заполнением базы"""
        response = cli.get(
            "/v1/user/1",
            headers={"Authorization": "Bearer xxx"},
        )
        assert response.status_code == 200
        data = response.json()
        logger.info(data)

    async def test_admin_not_auth_get_user(
        self,
        cli: TestClient,
        user_for_test1,  # fixture add user
        clear_db,  # если очистить базу после теста
    ) -> None:
        """Тестирует ручку /user с предварительным заполнением базы"""
        response = cli.get(
            "/v1/user/1",
            headers={},
        )
        assert response.status_code == 401

    async def test_admin_no_data_get_user(
        self,
        cli: TestClient,
        clear_db,  # если очистить базу после теста
    ) -> None:
        """Тестирует ручку get /user"""
        response = cli.get(
            "/v1/user",
            headers={"Authorization": "Bearer xxx"},
        )
        assert response.status_code == 404

    async def test_correct_quiz_add(
        self,
        cli: TestClient,
        clear_db,  # если очистить базу после теста
    ):
        """Тестирует ручку /quiz-add"""
        data_to_add = [
            {
                "question": "string",
                "answer": "string",
                "price": 100,
                "category": "common",
            }
        ]

        response = cli.post(
            "/v1/quiz-add",
            headers={"Authorization": "Bearer xxx"},
            json=data_to_add,
        )
        if response.status_code not in (200, 201):
            logger.error(response.json())
        assert response.status_code == 200
        data_resp = response.json()
        logger.info(data_resp)

    async def test_incorrect_quiz_add_no_data(
        self,
        cli: TestClient,
        clear_db,  # если очистить базу после теста
    ):
        """Тестирует ручку /quiz-add"""
        data_to_add = []
        response = cli.post(
            "/v1/quiz-add",
            headers={"Authorization": "Bearer xxx"},
            json=data_to_add,
        )
        assert response.status_code == 400

    async def test_incorrect_quiz_add(
        self,
        cli: TestClient,
        clear_db,  # если очистить базу после теста
    ):
        """Тестирует ручку /quiz-add"""
        data_to_add = [
            {
                "question": "string",
                "answer": "string",
                "price": 100,
                "category": "category",
            }
        ]

        for key, val in (
            ("category", "aaa"),
            ("price", -1),
            ("question", ""),
            ("answer", ""),
        ):
            wrong_data = data_to_add[0].copy()
            wrong_data[key] = val
            response = cli.post(
                "/v1/quiz-add",
                headers={"Authorization": "Bearer xxx"},
                json=data_to_add,
            )
            assert response.status_code == 422, response.status_code

    async def test_unauth_quiz_add(
        self,
        cli: TestClient,
        clear_db,  # если очистить базу после теста
    ):
        """Тестирует ручку /quiz-add"""
        data_to_add = [
            {
                "question": "string",
                "answer": "string",
                "price": 100,
                "category": "common",
            }
        ]

        response = cli.post(
            "/v1/quiz-add",
            headers={},
            json=data_to_add,
        )
        assert response.status_code == 401
        data_resp = response.json()
        logger.info(data_resp)
