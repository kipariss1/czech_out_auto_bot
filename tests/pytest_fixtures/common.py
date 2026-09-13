import pytest
from unittest.mock import patch
from typing import Any, Dict, Callable, TypedDict, Literal, List
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from src.models.models import Base
from datetime import datetime
import responses
import pathlib

JSON = Dict[str, Any]


@compiles(JSONB, "sqlite")
def _compile_jsonb_as_json_for_sqlite(element, compiler, **kw):
    # src/models/models.py uses Postgres JSONB columns whenever settings.is_postgres_env is
    # True (which now includes ENV=test, since ENV=test targets a real Postgres container).
    # This in-memory mock always runs on SQLite regardless of ENV, so JSONB columns need a
    # SQLite-renderable equivalent to create the schema at all.
    return "JSON"

class MockURL(TypedDict):
    type: Literal[responses.GET, responses.POST, responses.PUT, responses.PATCH, responses.DELETE]
    mock_url: str
    mock_html_path: pathlib.Path 
    status: int

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

@pytest.fixture(scope='function')
def build_mock_bazos() -> Callable[[List[MockURL]], responses.RequestsMock]:
    rsps = responses.RequestsMock(assert_all_requests_are_fired=False)
    rsps.start()
    def factory(urls2mock: List[MockURL]) -> responses.RequestsMock:
        for obj in urls2mock:
            with open(obj['mock_html_path'], encoding="utf-8") as f:
                html = f.read()
            rsps.add(
                obj['type'],
                obj['mock_url'],
                body=html,
                status=obj['status']
            )
        return rsps
    yield factory
    rsps.stop()
    rsps.reset()