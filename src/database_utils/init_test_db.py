from src.database_utils import db_handler
from src.models.models import CarSearch, User


def create_new_users(db=db_handler.get_db_connection()):
    new_user = User(
        id=1,
        telegram_id=368512732
    )
    db.add(new_user)
    db.commit()
    new_user = User(
        id=2,
        telegram_id=1111111111
    )
    db.add(new_user)
    db.commit()

def create_new_searches(db=db_handler.get_db_connection()):
    new_car_search = CarSearch(
        user_id=1.,
        car_model_id=112,
        psc_code="110 00",
        psc_km_range="25",
        year_range_from="2018",
        year_range_to="2026",
        milage_range_from="0",
        milage_range_to="200000",
        price_range_from="800000",
        price_range_to="1000000",
    )
    db.add(new_car_search)
    db.commit()
    # ------------------------------
    new_car_search = CarSearch(
        user_id=2.,
        car_model_id=112,
        psc_code="110 00",
        psc_km_range="25",
        year_range_from="2010",
        year_range_to="2018",
        milage_range_from="0",
        milage_range_to="50000",
        price_range_from="300000",
        price_range_to="7000000",
    )
    db.add(new_car_search)
    db.commit()
    # ------------------------------
    new_car_search = CarSearch(
        user_id=2.,
        car_model_id=226,
        psc_code="110 00",
        psc_km_range="25",
        year_range_from="2010",
        year_range_to="2018",
        milage_range_from="0",
        milage_range_to="50000",
        price_range_from="800000",
        price_range_to="1000000",
    )
    db.add(new_car_search)
    db.commit()

db_handler.create_tables()
db_handler.updload_cars_to_db()
create_new_users()
create_new_searches()


