from unittest.mock import AsyncMock

import pytest

from service.config import Storage


@pytest.fixture
def vk_api_send_message_mock(storage: Storage) -> AsyncMock:
    mock = AsyncMock()
    storage.vk_api.send_message = mock
    return mock
