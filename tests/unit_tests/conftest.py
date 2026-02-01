import pytest
from unittest.mock import MagicMock, patch
from typing import Any, Dict, Callable
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from src.models.models import Base
from datetime import datetime

JSON = Dict[str, Any]

@pytest.fixture(scope='function')
def build_mock_db() -> Callable[[str, JSON], Session]:
    def convert_rows_to_correct_dtypes(rows: list[dict]):
        conversion_mapping = {
            "#ConvertStr2Datetime": datetime.fromisoformat,
        }
        for row in rows:
            for k, v in row.items():
                for tag, conv_strategy in conversion_mapping.items():
                    if type(v) == str and tag in v:
                        row[k] = conv_strategy(v.replace(tag, '').strip(' '))

    def factory(path: str, data: JSON) -> Session:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        mock_db = Session()
        for table_name, rows in data.items():
            model = Base.metadata.tables[table_name]
            convert_rows_to_correct_dtypes(rows)
            mock_db.execute(model.insert(), rows)
        patch(path, return_value=mock_db).start()
        return mock_db
    return factory