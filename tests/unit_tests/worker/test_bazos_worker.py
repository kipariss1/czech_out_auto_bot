from datetime import datetime, timedelta, timezone

from queue_svc.worker.bazos_worker import BazosWorker
from src.models.models import ParsedAdvertisementCache
from src.settings.settings import settings


VALID_RESULT = {
    "is_valid_ad": True,
    "brand": "BMW",
    "model": "F20",
    "engine": "B47",
    "year": "2016",
    "mileage": "70000",
}


def _build_worker(monkeypatch, build_mock_db, extra_rows=None):
    mock_data = {
        "Car_Models": [{"id": 1, "manufacturer": "BMW", "model": "F20"}],
    }
    if extra_rows:
        mock_data.update(extra_rows)
    mock_db = build_mock_db(
        "queue_svc.worker.bazos_worker.db_handler.get_db_connection",
        mock_data,
    )
    monkeypatch.setattr(
        "queue_svc.worker.bazos_worker.db_handler.get_db_connection",
        lambda: mock_db,
    )
    worker = BazosWorker()
    return worker, mock_db


def test_get_cached_parse_result_returns_stored_result_when_fresh(monkeypatch, build_mock_db):
    worker, mock_db = _build_worker(
        monkeypatch,
        build_mock_db,
        {
            "Parsed_Advertisements_Cache": [
                {"id": 1, "bazos_id": 111, "car_id": 1, "parsed_result": VALID_RESULT},
            ],
        },
    )

    result = worker._get_cached_parse_result("111", 1)

    assert result == VALID_RESULT


def test_get_cached_parse_result_returns_none_when_no_row(monkeypatch, build_mock_db):
    worker, mock_db = _build_worker(monkeypatch, build_mock_db)

    assert worker._get_cached_parse_result("111", 1) is None


def test_get_cached_parse_result_returns_none_when_expired(monkeypatch, build_mock_db):
    stale_cached_at = datetime.now(timezone.utc) - timedelta(
        days=settings.parsed_ad_cache_retention_days + 5
    )
    worker, mock_db = _build_worker(
        monkeypatch,
        build_mock_db,
        {
            "Parsed_Advertisements_Cache": [
                {
                    "id": 1,
                    "bazos_id": 111,
                    "car_id": 1,
                    "parsed_result": VALID_RESULT,
                    "cached_at": f"#ConvertStr2Datetime {stale_cached_at.isoformat()}",
                },
            ],
        },
    )

    assert worker._get_cached_parse_result("111", 1) is None


def test_save_parsed_result_to_cache_inserts_when_missing(monkeypatch, build_mock_db):
    worker, mock_db = _build_worker(monkeypatch, build_mock_db)

    worker._save_parsed_result_to_cache("111", 1, VALID_RESULT)

    rows = mock_db.query(ParsedAdvertisementCache).all()
    assert len(rows) == 1
    assert rows[0].bazos_id == 111
    assert rows[0].car_id == 1
    assert rows[0].parsed_result == VALID_RESULT


def test_save_parsed_result_to_cache_updates_existing_row_in_place(monkeypatch, build_mock_db):
    worker, mock_db = _build_worker(
        monkeypatch,
        build_mock_db,
        {
            "Parsed_Advertisements_Cache": [
                {"id": 1, "bazos_id": 111, "car_id": 1, "parsed_result": {"is_valid_ad": False}},
            ],
        },
    )

    worker._save_parsed_result_to_cache("111", 1, VALID_RESULT)

    rows = mock_db.query(ParsedAdvertisementCache).all()
    assert len(rows) == 1
    assert rows[0].id == 1
    assert rows[0].parsed_result == VALID_RESULT
