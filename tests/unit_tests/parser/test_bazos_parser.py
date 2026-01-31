from parser.bazos_parser import BazosParser
import pytest
import json


def test_bazos_parser_correctly_finds_the_last_checked_ad(build_mock_db):
    with open("tests/unit_tests/test_data/test_bazos_parser_correctly_finds_the_last_checked_ad.json") as f:
        text = f.read()
    mock_data = json.loads(text)
    mock_db = build_mock_db(
        "parser.bazos_parser.db_handler.get_db_connection",
        mock_data
    )
    bp = BazosParser()
    bp.parse()
    




def test_bazos_parser_doesnt_lose_older_ads_if_price_margins_changed():
    pass

def bazos_parser_correctly_sets_an_lower_price_range():
    # 10% из верхней границы если нижняя не установлена
    pass


