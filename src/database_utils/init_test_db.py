from src.database_utils import db_handler
from src.models.models import CarSearch, User


def create_new_users(db=db_handler.get_db_connection()):
    new_user = User(
        id=1
    )
    db.add(new_user)
    db.commit()

def create_new_searches(db=db_handler.get_db_connection()):
    attributes = {
        "input_year_range_from": "2010",
        "input_year_range_to": "2018",
        "input_mileage_range_from": "0",
        "input_mileage_range_to": "50000",
        "input_price_range_from": "800000",
        "input_price_range_to": "1000000"
    }
    new_car_search = CarSearch(
        user_id=1.,
        car_model_id=112,
        psc_code="110 00",
        psc_km_range="25",
        attributes=attributes
    )
    db.add(new_car_search)
    db.commit()

db_handler.create_tables()
db_handler.updload_cars_to_db()
create_new_users()
create_new_searches()


