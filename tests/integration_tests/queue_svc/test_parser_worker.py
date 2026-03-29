import asyncio
from unittest.mock import AsyncMock, Mock

import responses

from queue_svc.parser.bazos_parser import BazosParser
from queue_svc.worker.bazos_worker import BazosWorker
from src.models.models import AdQueue


TOPED_AD_1 = "https://auto.bazos.cz/inzerat/213142446/f20-188i-urban-line.php"
TOPED_AD_2 = "https://auto.bazos.cz/inzerat/214086678/prodam-motor-b47d20b-z-bmw-x5-f15-25dx-170kw-najeto-70tis-km.php"
TOPED_AD_3 = "https://auto.bazos.cz/inzerat/214085280/prodam-motor-n55b30a-f30-335i-f31-f20-135i-f10-535i-f25-35i.php"
TOPED_AD_4 = "https://auto.bazos.cz/inzerat/213577477/bmw-f20-118i-b38-mpaket.php"
REGULAR_AD_1 = "https://auto.bazos.cz/inzerat/214330574/bmw-rada-1-bmw-f20-116ed-2013-manual.php"
REGULAR_AD_2 = "https://auto.bazos.cz/inzerat/214321960/predam-kompletny-motor-s-oznacenym-n47d20d-160kw.php"
REGULAR_AD_3 = "https://auto.bazos.cz/inzerat/214321906/predam-kompletny-motor-n55-n55b30a-nove-rozvody-loziska.php"
REGULAR_AD_4 = "https://auto.bazos.cz/inzerat/214306962/bmw-f20-116d-20d-85-kw.php"
PAGE2_AD_1 = "https://auto.bazos.cz/inzerat/213641524/bmw-f20-20d-2013.php"
PAGE2_AD_4 = "https://auto.bazos.cz/inzerat/213232408/bmw-rad-1-model-f20.php"

TOPED_ADS = {TOPED_AD_1, TOPED_AD_2, TOPED_AD_3, TOPED_AD_4}


def _mock_bazos_pages(build_mock_bazos, min_from_price: int, max_to_price: int):
    return build_mock_bazos(
        [
            {
                "type": responses.GET,
                "mock_url": (
                    "https://auto.bazos.cz/"
                    "?hledat=BMW+F20&rubriky=auto&hlokalita=&humkreis=25"
                    f"&cenaod={min_from_price}&cenado={max_to_price}&Submit=Hledat"
                    "&order=&crp=&kitx=ano"
                ),
                "mock_html_path": (
                    "tests/integration_tests/test_data/test_parser_worker/page1.html"
                ),
                "status": 200,
            },
            {
                'type': responses.GET,
                'mock_url': (
                    "https://auto.bazos.cz/20/"
                    "?hledat=BMW+F20&hlokalita=&humkreis=25"
                    f"&cenaod={min_from_price}&cenado={max_to_price}&order="
                ),
                'mock_html_path': "tests/integration_tests/test_data/test_parser_worker/page2.html",
                'status': 200
            }
        ]
    )


def _build_parser_and_worker(monkeypatch, build_mock_db, mock_data):
    mock_db = build_mock_db(
        "queue_svc.parser.bazos_parser.db_handler.get_db_connection",
        mock_data,
    )
    monkeypatch.setattr(
        "queue_svc.worker.bazos_worker.db_handler.get_db_connection",
        lambda: mock_db,
    )
    parser = BazosParser()
    worker = BazosWorker()
    send_message = Mock()
    monkeypatch.setattr("queue_svc.worker.bazos_worker.bot.send_message", send_message)
    return mock_db, parser, worker, send_message


def _mock_ad_methods(monkeypatch, ad_payloads):
    async def fake_get_page_text(self):
        payload = ad_payloads.get(
            self.link,
            {"text": f"unmatched:{self.link}", "price": 999999},
        )
        self.text = payload["text"]
        self.price = payload["price"]
        self.psc = payload.get("psc", "110 00")

    async def fake_is_toped(self):
        return self.link in TOPED_ADS

    monkeypatch.setattr(
        "queue_svc.bazos_api.auto_bazos_api.AutoAdvertisementPage.get_page_text",
        fake_get_page_text,
    )
    monkeypatch.setattr(
        "queue_svc.bazos_api.auto_bazos_api.AutoAdvertisementPage.is_toped",
        fake_is_toped,
    )
    monkeypatch.setattr(
        "queue_svc.bazos_api.auto_bazos_api.AutoAdvertisementPage.is_deleted",
        AsyncMock(return_value=False),
    )


def _notification_calls(send_message):
    return [
        {
            "chat_id": call.kwargs["chat_id"],
            "text": call.kwargs["text"],
        }
        for call in send_message.call_args_list
    ]


def test_newly_created_searches(monkeypatch, build_mock_db, build_mock_bazos):
    mock_data = {
        "Users": [
            {"id": 1, "telegram_id": 111111111},
            {"id": 2, "telegram_id": 222222222},
        ],
        "Car_Models": [
            {
                "id": 1,
                "manufacturer": "BMW",
                "model": "F20",
                "_last_checked_links": [PAGE2_AD_4],
            },
        ],
        "Car_Searches": [
            {
                "id": 1,
                "user_id": 1,
                "car_model_id": 1,
                "psc_code": "110 00",
                "psc_km_range": "25",
                "year_range_from": 2016,
                "year_range_to": 2020,
                "mileage_range_from": 1000,
                "mileage_range_to": 30000,
                "price_range_from": 180000,
                "price_range_to": 260000,
            },
            {
                "id": 2,
                "user_id": 2,
                "car_model_id": 1,
                "psc_code": "110 00",
                "psc_km_range": "25",
                "year_range_from": 2012,
                "year_range_to": 2015,
                "mileage_range_from": 40000,
                "mileage_range_to": 90000,
                "price_range_from": 120000,
                "price_range_to": 190000,
            },
        ],
    }
    _mock_bazos_pages(build_mock_bazos, 120000, 260000)
    ad_payloads = {
        TOPED_AD_1: {"text": "ad-for-user-1", "price": 220000},
        TOPED_AD_2: {"text": "miss-toped", "price": 450000},
        TOPED_AD_3: {"text": "miss-toped-2", "price": 90000},
        TOPED_AD_4: {"text": "miss-toped-3", "price": 500000},
        REGULAR_AD_1: {"text": "miss-regular-1", "price": 170000},
        REGULAR_AD_2: {"text": "miss-regular-2", "price": 310000},
        REGULAR_AD_3: {"text": "miss-regular-3", "price": 410000},
        REGULAR_AD_4: {"text": "miss-regular-4", "price": 280000},
        PAGE2_AD_1: {"text": "ad-for-user-2", "price": 150000},
    }
    default_response = {"is_valid_ad": False}
    ollama_responses = {
        "ad-for-user-1": {
            "is_valid_ad": True,
            "brand": "BMW",
            "model": "F20",
            "engine": "B48",
            "year": "2018",
            "mileage": "15000",
            "price": "220000",
        },
        "ad-for-user-2": {
            "is_valid_ad": True,
            "brand": "BMW",
            "model": "F20",
            "engine": "B47",
            "year": "2013",
            "mileage": "60000",
            "price": "150000",
        },
    }

    mock_db, parser, worker, send_message = _build_parser_and_worker(
        monkeypatch,
        build_mock_db,
        mock_data,
    )
    _mock_ad_methods(monkeypatch, ad_payloads)
    worker.ollama = Mock(
        process=Mock(
            side_effect=lambda ad_text, car: ollama_responses.get(ad_text, default_response).copy()
        )
    )

    asyncio.run(parser.parse())

    row = mock_db.query(AdQueue).filter(AdQueue.car_model_id == 1).first()
    assert TOPED_AD_1 in row.queue
    assert PAGE2_AD_1 in row.queue

    asyncio.run(worker.process_queue())

    calls = _notification_calls(send_message)
    assert len(calls) == 2
    assert any(call["chat_id"] == 111111111 and TOPED_AD_1 in call["text"] for call in calls)
    assert any(call["chat_id"] == 222222222 and PAGE2_AD_1 in call["text"] for call in calls)
    assert row.queue == []


def test_already_created_searches(monkeypatch, build_mock_db, build_mock_bazos):
    mock_data = {
        "Users": [
            {"id": 1, "telegram_id": 111111111},
            {"id": 2, "telegram_id": 222222222},
        ],
        "Car_Models": [
            {
                "id": 1,
                "manufacturer": "BMW",
                "model": "F20",
                "_last_checked_toped_links": [TOPED_AD_1, TOPED_AD_2],
                "_last_checked_links": [PAGE2_AD_4, REGULAR_AD_1, REGULAR_AD_2, REGULAR_AD_3],
            },
        ],
        "Car_Searches": [
            {
                "id": 1,
                "user_id": 1,
                "car_model_id": 1,
                "psc_code": "110 00",
                "psc_km_range": "25",
                "year_range_from": 2010,
                "year_range_to": 2020,
                "mileage_range_from": 0,
                "mileage_range_to": 120000,
                "price_range_from": 100000,
                "price_range_to": 400000,
            },
            {
                "id": 2,
                "user_id": 2,
                "car_model_id": 1,
                "psc_code": "110 00",
                "psc_km_range": "25",
                "year_range_from": 2022,
                "year_range_to": 2026,
                "mileage_range_from": 0,
                "mileage_range_to": 10000,
                "price_range_from": 500000,
                "price_range_to": 800000,
            },
        ],
    }
    _mock_bazos_pages(build_mock_bazos, 100000, 800000)
    ad_payloads = {
        TOPED_AD_1: {"text": "checked-toped-fit", "price": 220000},
        TOPED_AD_3: {"text": "unchecked-toped-miss", "price": 90000},
        TOPED_AD_4: {"text": "unchecked-toped-fit", "price": 230000},
        REGULAR_AD_1: {"text": "checked-regular-fit", "price": 180000},
        REGULAR_AD_2: {"text": "checked-regular-miss", "price": 450000},
        REGULAR_AD_3: {"text": "checked-regular-miss-2", "price": 470000},
        REGULAR_AD_4: {"text": "unchecked-regular-fit", "price": 210000},
        PAGE2_AD_1: {"text": "unchecked-regular-miss", "price": 90000},
    }
    default_response = {"is_valid_ad": False}
    ollama_responses = {
        "checked-toped-fit": {
            "is_valid_ad": True,
            "brand": "BMW",
            "model": "F20",
            "engine": "B48",
            "year": "2018",
            "mileage": "20000",
            "price": "220000",
        },
        "unchecked-toped-miss": {
            "is_valid_ad": True,
            "brand": "BMW",
            "model": "F20",
            "engine": "N55",
            "year": "2011",
            "mileage": "90000",
            "price": "90000",
        },
        "unchecked-toped-fit": {
            "is_valid_ad": True,
            "brand": "BMW",
            "model": "F20",
            "engine": "B38",
            "year": "2017",
            "mileage": "45000",
            "price": "230000",
        },
        "checked-regular-fit": {
            "is_valid_ad": True,
            "brand": "BMW",
            "model": "F20",
            "engine": "B47",
            "year": "2016",
            "mileage": "70000",
            "price": "180000",
        },
        "unchecked-regular-fit": {
            "is_valid_ad": True,
            "brand": "BMW",
            "model": "F20",
            "engine": "B47",
            "year": "2016",
            "mileage": "70000",
            "price": "210000",
        },
        "unchecked-regular-miss": {
            "is_valid_ad": True,
            "brand": "BMW",
            "model": "F20",
            "engine": "B47",
            "year": "2014",
            "mileage": "80000",
            "price": "90000",
        },
    }

    mock_db, parser, worker, send_message = _build_parser_and_worker(
        monkeypatch,
        build_mock_db,
        mock_data,
    )
    _mock_ad_methods(monkeypatch, ad_payloads)
    worker.ollama = Mock(
        process=Mock(
            side_effect=lambda ad_text, car: ollama_responses.get(ad_text, default_response).copy()
        )
    )

    asyncio.run(parser.parse())

    row = mock_db.query(AdQueue).filter(AdQueue.car_model_id == 1).first()
    assert TOPED_AD_1 not in row.queue
    assert TOPED_AD_2 not in row.queue
    assert REGULAR_AD_1 in row.queue
    assert REGULAR_AD_2 in row.queue
    assert REGULAR_AD_3 in row.queue
    assert TOPED_AD_4 in row.queue
    assert REGULAR_AD_4 in row.queue

    asyncio.run(worker.process_queue())

    calls = _notification_calls(send_message)
    assert len(calls) == 2
    assert any(call["chat_id"] == 111111111 and TOPED_AD_4 in call["text"] for call in calls)
    assert any(call["chat_id"] == 111111111 and REGULAR_AD_4 in call["text"] for call in calls)
    assert all(TOPED_AD_1 not in call["text"] for call in calls)
    assert all(REGULAR_AD_1 not in call["text"] for call in calls)
    assert row.queue == []
