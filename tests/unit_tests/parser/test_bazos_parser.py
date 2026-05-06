from queue_svc.parser.bazos_parser import BazosParser
from src.models.models import AdQueue
from typing import List
from unittest.mock import AsyncMock
from tests.pytest_fixtures.common import MockURL
import pytest
import json
import responses
import asyncio

@pytest.fixture
def mock_bazos(build_mock_bazos):
    urls2mock = [
        {
            'type': responses.GET,
            'mock_url': (
                "https://auto.bazos.cz/"
                "?hledat=BMW+F20&rubriky=auto&hlokalita=110+00&humkreis=25"
                "&cenaod=100000&cenado=400000&Submit=Hledat"
                "&order=&crp=&kitx=ano"
            ),
            'mock_html_path': "tests/unit_tests/test_data/test_bazos_parser_correctly_finds_the_last_checked_ad/page1.html",
            'status': 200
        },
        {
            'type': responses.GET,
            'mock_url': (
                "https://auto.bazos.cz/20/"
                "?hledat=BMW+F20&hlokalita=110+00&humkreis=25"
                "&cenaod=100000&cenado=400000&order="
            ),
            'mock_html_path': "tests/unit_tests/test_data/test_bazos_parser_correctly_finds_the_last_checked_ad/page2.html",
            'status': 200
        }
    ]
    yield build_mock_bazos(urls2mock)

@pytest.fixture
def asserted_queue():
    return [
        'https://auto.bazos.cz/inzerat/213142446/f20-188i-urban-line.php', 
        'https://auto.bazos.cz/inzerat/214086678/prodam-motor-b47d20b-z-bmw-x5-f15-25dx-170kw-najeto-70tis-km.php', 
        'https://auto.bazos.cz/inzerat/214085280/prodam-motor-n55b30a-f30-335i-f31-f20-135i-f10-535i-f25-35i.php', 
        'https://auto.bazos.cz/inzerat/213577477/bmw-f20-118i-b38-mpaket.php', 
        'https://auto.bazos.cz/inzerat/214330574/bmw-rada-1-bmw-f20-116ed-2013-manual.php', 
        'https://auto.bazos.cz/inzerat/214321960/predam-kompletny-motor-s-oznacenym-n47d20d-160kw.php', 
        'https://auto.bazos.cz/inzerat/214321906/predam-kompletny-motor-n55-n55b30a-nove-rozvody-loziska.php', 
        'https://auto.bazos.cz/inzerat/214306962/bmw-f20-116d-20d-85-kw.php', 
        'https://auto.bazos.cz/inzerat/214228476/bmw-f20-116d-85-kw.php', 
        'https://auto.bazos.cz/inzerat/213774086/bmw-f20-f21-m135i-f22-m235i-motor-n55-n55b30a.php', 
        'https://auto.bazos.cz/inzerat/213596962/bmw-f20-f21-f22-motor-n55b30a-nove-rozvody-240kw.php', 
        'https://auto.bazos.cz/inzerat/212838480/bmw-116d-urban-model-f20.php', 
        'https://auto.bazos.cz/inzerat/214032404/bmw-116i-80-kw.php', 
        'https://auto.bazos.cz/inzerat/213467912/bmw-1-118d-f20-2013-m-paket.php', 
        'https://auto.bazos.cz/inzerat/212932605/bmw-116-i-2012.php', 
        'https://auto.bazos.cz/inzerat/212677088/bmw-1-f20-116d-rv-2015-99-tis-kmm-paket.php', 
        'https://auto.bazos.cz/inzerat/213788116/bmw-120d-f20.php', 
        'https://auto.bazos.cz/inzerat/213761480/bmw-e92-335i.php', 
        'https://auto.bazos.cz/inzerat/213759936/bmw-rada-1-20d-rv-32013-najeto-201130-km.php', 
        'https://auto.bazos.cz/inzerat/212022352/bmw-f20-118d-20d-105kw-zf.php', 
        'https://auto.bazos.cz/inzerat/213641524/bmw-f20-20d-2013.php', 
        'https://auto.bazos.cz/inzerat/213355388/bmw-1-116d-85kw-f20-n47-kuze.php', 
        'https://auto.bazos.cz/inzerat/213281536/bmw-116d-f20.php']


@pytest.fixture
def asserted_queue_without_checked_toped_ads(asserted_queue):
    return asserted_queue[2:]

@pytest.fixture
def mock_data_with_checked_toped_ads():
    with open("tests/unit_tests/test_data/test_bazos_parser_correctly_finds_the_last_checked_ad/mock_data_toped.json") as f:
        text = f.read()
    mock_data = json.loads(text)
    return mock_data

@pytest.fixture
def mock_data():
    with open("tests/unit_tests/test_data/test_bazos_parser_correctly_finds_the_last_checked_ad/mock_data.json") as f:
        text = f.read()
    mock_data = json.loads(text)
    return mock_data

def test_bazos_parser_correctly_finds_the_last_checked_ad(monkeypatch, build_mock_db, mock_bazos, asserted_queue, mock_data):
    search_id = int(mock_data["Car_Searches"][0]["id"])
    mock_db = build_mock_db(
        "queue_svc.parser.bazos_parser.db_handler.get_db_connection",
        mock_data
    )
    monkeypatch.setattr(
        "queue_svc.bazos_api.auto_bazos_api.AutoAdvertisementPage.is_toped",
        AsyncMock(side_effect=[True]*4 + [False]*(len(asserted_queue) - 4))
    )
    monkeypatch.setattr(
        "queue_svc.bazos_api.auto_bazos_api.AutoAdvertisementPage.is_deleted",
        AsyncMock(side_effect=lambda : False)
    )
    bp = BazosParser()
    asyncio.run(bp.parse())
    queue = (
        mock_db.query(AdQueue.queue)
        .filter(AdQueue.car_search_id == search_id)
        .scalar()
    )
    assert queue == asserted_queue

def test_topped_adds_are_processed_separately(
        monkeypatch, 
        build_mock_db, 
        mock_bazos, 
        asserted_queue_without_checked_toped_ads,
        asserted_queue,
        mock_data_with_checked_toped_ads,
    ):
    search_id = int(mock_data_with_checked_toped_ads["Car_Searches"][0]["id"])
    mock_db = build_mock_db(
        "queue_svc.parser.bazos_parser.db_handler.get_db_connection",
        mock_data_with_checked_toped_ads
    )
    monkeypatch.setattr(
        "queue_svc.bazos_api.auto_bazos_api.AutoAdvertisementPage.is_toped",
        AsyncMock(side_effect=[True]*4 + [False]*(len(asserted_queue) - 4))
    )
    monkeypatch.setattr(
        "queue_svc.bazos_api.auto_bazos_api.AutoAdvertisementPage.is_deleted",
        AsyncMock(side_effect=lambda : False)
    )
    bp = BazosParser()
    asyncio.run(bp.parse())
    queue = (
        mock_db.query(AdQueue.queue)
        .filter(AdQueue.car_search_id == search_id)
        .scalar()
    )
    assert queue == asserted_queue_without_checked_toped_ads

def test_new_search_collects_ads_from_last_page_to_first(build_mock_db, mock_bazos, asserted_queue):
    car_id = 1
    mock_data = {
        "Users": [
            {"id": 1, "telegram_id": 111111111},
        ],
        "Car_Models": [
            {
                "id": car_id,
                "manufacturer": "BMW",
                "model": "F20",
            },
        ],
        "Car_Searches": [
            {
                "id": 1,
                "user_id": 1,
                "car_model_id": car_id,
                "psc_code": "110 00",
                "psc_km_range": "25",
                "year_range_from": 2010,
                "year_range_to": 2020,
                "mileage_range_from": 0,
                "mileage_range_to": 120000,
                "price_range_from": 100000,
                "price_range_to": 400000,
                "_last_checked_links": [],
                "_last_checked_toped_links": [],
            },
        ],
    }
    mock_db = build_mock_db(
        "queue_svc.parser.bazos_parser.db_handler.get_db_connection",
        mock_data
    )
    bp = BazosParser()
    asyncio.run(bp.parse())
    queue = (
        mock_db.query(AdQueue.queue)
        .filter(AdQueue.car_search_id == 1)
        .scalar()
    )

    assert len(queue) == 35
    assert queue[:3] == asserted_queue[20:]
    assert queue[15:] == asserted_queue[:20]

def test_deleted_adds_in_last_checked_links_are_processed_correctly(monkeypatch, build_mock_db, mock_bazos, asserted_queue, mock_data):
    asserted_queue.append("https://auto.bazos.cz/inzerat/213232408/bmw-rad-1-model-f20.php")
    search_id = int(mock_data["Car_Searches"][0]["id"])
    mock_db = build_mock_db(
        "queue_svc.parser.bazos_parser.db_handler.get_db_connection",
        mock_data
    )
    monkeypatch.setattr(
        "queue_svc.bazos_api.auto_bazos_api.AutoAdvertisementPage.is_toped",
        AsyncMock(side_effect=[True]*4 + [False]*(len(asserted_queue) - 4))
    )
    monkeypatch.setattr(
        "queue_svc.bazos_api.auto_bazos_api.AutoAdvertisementPage.is_deleted",
        AsyncMock(side_effect=[True, False, False])
    )
    bp = BazosParser()
    asyncio.run(bp.parse())
    queue = (
        mock_db.query(AdQueue.queue)
        .filter(AdQueue.car_search_id == search_id)
        .scalar()
    )
    assert queue == asserted_queue
