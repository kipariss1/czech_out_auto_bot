from parser.bazos_parser import BazosParser
from src.models.models import AdQueue
import pytest
import json
import responses
import asyncio


@pytest.fixture
def mock_bazos():
    with responses.RequestsMock() as rsps:
        url_page_1 = (
            "https://auto.bazos.cz/"
            "?hledat=BMW+F20&rubriky=auto&hlokalita=None&humkreis=None"
            "&cenaod=100000&cenado=400000&Submit=Hledat"
            "&order=&crp=&kitx=ano"
        )
        url_page_2 = (
            "https://auto.bazos.cz/20/"
            "?hledat=BMW+F20&rubriky=auto&hlokalita=None&humkreis=None"
            "&cenaod=100000&cenado=400000&&Submit=Hledat"
            "&order=&crp=&kitx=ano"
        )
        with open("tests/unit_tests/test_data/test_bazos_parser_correctly_finds_the_last_checked_ad/page1.html", encoding="utf-8") as f:
            page1 = f.read()
        with open("tests/unit_tests/test_data/test_bazos_parser_correctly_finds_the_last_checked_ad/page2.html", encoding="utf-8") as f:
            page2 = f.read()
        rsps.add(
            responses.GET,
            url_page_1,
            body=page1,
            status=200,
        )
        rsps.add(
            responses.GET,
            url_page_2,
            body=page2,
            status=200,
        )
        yield rsps


def test_bazos_parser_correctly_finds_the_last_checked_ad(build_mock_db, mock_bazos):
    with open("tests/unit_tests/test_data/test_bazos_parser_correctly_finds_the_last_checked_ad/mock_data.json") as f:
        text = f.read()
    mock_data = json.loads(text)
    car_id = mock_data["Car_Models"][0]["id"]
    mock_db = build_mock_db(
        "parser.bazos_parser.db_handler.get_db_connection",
        mock_data
    )
    bp = BazosParser()
    asyncio.run(bp.parse())
    queue = (
        mock_db.query(AdQueue.queue)
        .filter(AdQueue.car_model_id == car_id)
        .scalar()
    )
    assert queue == [
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

def test_bazos_parser_doesnt_lose_older_ads_if_price_margins_changed():
    pass

def test_bazos_parser_correctly_sets_an_lower_price_range():
    # 10% из верхней границы если нижняя не установлена
    pass


