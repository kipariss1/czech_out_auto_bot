from parser.bazos_parser import BazosParser
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
    mock_db = build_mock_db(
        "parser.bazos_parser.db_handler.get_db_connection",
        mock_data
    )
    bp = BazosParser()
    asyncio.run(bp.parse())
    




def test_bazos_parser_doesnt_lose_older_ads_if_price_margins_changed():
    pass

def test_bazos_parser_correctly_sets_an_lower_price_range():
    # 10% из верхней границы если нижняя не установлена
    pass


