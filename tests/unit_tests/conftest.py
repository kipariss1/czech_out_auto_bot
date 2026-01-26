import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture(scope='function')
def build_mock_db():
    def factory(path, tables):
        mock_db = MagicMock()
        # TODO: здесь прокинуть данные в тестовую дб
        with patch(path, return_value=mock_db): 
            return mock_db
    return factory