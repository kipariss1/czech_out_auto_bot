import pytest
from unittest.mock import MagicMock, patch
from typing import Any, Dict, Callable
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from src.models.models import Base

JSON = Dict[str, Any]

@pytest.fixture(scope='function')
def build_mock_db() -> Callable[[str, JSON], Session]:
    def factory(path: str, data: JSON) -> Session:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        mock_db = Session()
        for table_name, rows in data.items():
            model = Base.metadata.tables[table_name]
            mock_db.execute(model.insert(), rows)
        with patch(path, return_value=mock_db): 
            return mock_db
    return factory