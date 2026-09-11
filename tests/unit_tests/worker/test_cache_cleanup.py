from datetime import datetime, timedelta, timezone

from queue_svc.worker.bazos_worker import BazosWorker
from src.models.models import ParsedAdvertisementCache
from src.settings.settings import settings


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


def test_cleanup_expired_cache_deletes_expired_and_keeps_fresh(monkeypatch, build_mock_db):
    stale_cached_at = datetime.now(timezone.utc) - timedelta(
        days=settings.parsed_ad_cache_retention_days + 5
    )
    fresh_cached_at = datetime.now(timezone.utc)
    worker, mock_db = _build_worker(
        monkeypatch,
        build_mock_db,
        {
            "Parsed_Advertisements_Cache": [
                {
                    "id": 1,
                    "bazos_id": 111,
                    "car_id": 1,
                    "parsed_result": {"is_valid_ad": False},
                    "cached_at": f"#ConvertStr2Datetime {stale_cached_at.isoformat()}",
                },
                {
                    "id": 2,
                    "bazos_id": 222,
                    "car_id": 1,
                    "parsed_result": {"is_valid_ad": False},
                    "cached_at": f"#ConvertStr2Datetime {fresh_cached_at.isoformat()}",
                },
            ],
        },
    )

    worker.cleanup_expired_cache()

    remaining = mock_db.query(ParsedAdvertisementCache).all()
    assert [row.bazos_id for row in remaining] == [222]


def test_cleanup_expired_cache_is_noop_when_nothing_expired(monkeypatch, build_mock_db):
    worker, mock_db = _build_worker(
        monkeypatch,
        build_mock_db,
        {
            "Parsed_Advertisements_Cache": [
                {"id": 1, "bazos_id": 111, "car_id": 1, "parsed_result": {"is_valid_ad": False}},
            ],
        },
    )

    worker.cleanup_expired_cache()

    remaining = mock_db.query(ParsedAdvertisementCache).all()
    assert [row.bazos_id for row in remaining] == [111]
