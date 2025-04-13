import json
from src.scrap_car_models import add_car_models_to_db

with open("tests/global_fixtures/cars_fixture.json", "r") as f:
    cars = json.load(f)
    for company in cars["manufacturers"]:
        add_car_models_to_db(company["name"], company["models"])
