from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from starlette import requests
from sqlalchemy import and_
from sqlalchemy.orm import Session
from src.database_utils import db_handler 
from src.models.models import CarModel, User
from fastapi.templating import Jinja2Templates
from typing import List
from src.models.models import CarSearchCreate, CarSearch
from web_app import BASE_DIR


router = APIRouter()
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def _get_user_by_telegram_id(db: Session, telegram_user_id: int) -> User | None:
    return db.query(User).filter(User.telegram_id == telegram_user_id).first()


def _get_or_create_user_by_telegram_id(db: Session, telegram_user_id: int) -> User:
    user = _get_user_by_telegram_id(db, telegram_user_id)
    if user is None:
        user = User(telegram_id=telegram_user_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@router.get("/searches/{telegram_user_id}")
def get_searches_by_id(
    telegram_user_id: int, db: Session = Depends(db_handler.get_db_connection)
):
    user = _get_user_by_telegram_id(db, telegram_user_id)
    if user is None:
        return JSONResponse([])

    searches = (
        db.query(CarSearch)
        .filter(CarSearch.user_id == user.id)
        .all()
    )
    return JSONResponse(list(map(lambda s: s.to_dict(), list(searches))))


@router.get("/")
def main_view(
    request: Request,
    new_search_created: bool = False,
    search_already_exists: bool = False,
):
    render_dict = {
        "request": request,
        "new_search_created": new_search_created,
        "search_already_exists": search_already_exists,
    }
    return templates.TemplateResponse("index.html", render_dict)


@router.get("/create_search", response_class=HTMLResponse)
def create_search_view(
    request: requests.Request,
    db: Session = Depends(db_handler.get_db_connection),
):
    unique_car_manufacturers = (
        db.query(CarModel.manufacturer)
        .distinct()
        .order_by(CarModel.manufacturer.asc())
        .all()
    )
    unique_car_manufacturers = list(map(lambda el: el[0], unique_car_manufacturers))
    render_dict = {"request": request, "car_manufacturers": unique_car_manufacturers}
    return templates.TemplateResponse("create_search.html", render_dict)


def _check_if_search_exists(
    db,
    user_id,
    car_model_id,
    psc_code,
    psc_km_range,
    year_range_from,
    year_range_to,
    mileage_range_from,
    mileage_range_to,
    price_range_from,
    price_range_to,
):
    existing_searches = db.query(CarSearch).filter(
        and_(
            CarSearch.user_id == user_id,
            CarSearch.car_model_id == car_model_id,
            CarSearch.psc_code == psc_code,
            CarSearch.year_range_from == year_range_from,
            CarSearch.year_range_to == year_range_to,
            CarSearch.mileage_range_from == mileage_range_from,
            CarSearch.mileage_range_to == mileage_range_to,
            CarSearch.price_range_from == price_range_from,
            CarSearch.price_range_to == price_range_to,
            CarSearch.psc_km_range == psc_km_range,
        )
    )
    if len(list(existing_searches)) > 0:
        return True
    return False


def _find_car_by_model(manufacturer: str, model: str):
    db = db_handler.get_db_connection()
    cars = db.query(CarModel).filter(
        and_(
            CarModel.manufacturer == manufacturer,
            CarModel.model == model,
        )
    )
    if len(list(cars)) != 1:
        raise Exception("The car name is not found or ambiguous")
    return cars


@router.post("/create_search", response_class=JSONResponse)
def post_create_search_view(
    request: CarSearchCreate,
    db: Session = Depends(db_handler.get_db_connection),
):
    user = _get_or_create_user_by_telegram_id(db, request.telegram_user_id)

    cars = _find_car_by_model(request.manufacturer, request.model)
    new_search_args = {
        "user_id": user.id,
        "car_model_id": cars[0].id,
        "psc_code": request.psc_code,
        "psc_km_range": request.psc_km_range,
        "year_range_from": int(request.input_year_range_from),
        "year_range_to": int(request.input_year_range_to),
        "mileage_range_from": int(request.input_mileage_range_from),
        "mileage_range_to": int(request.input_mileage_range_to),
        "price_range_from": int(request.input_price_range_from),
        "price_range_to": int(request.input_price_range_to),
    }
    if _check_if_search_exists(db, **new_search_args):
        return JSONResponse(
            {"search_created": False, "reason": "search already exists"}
        )
    new_search = CarSearch(**new_search_args)
    db.add(new_search)
    db.commit()
    return JSONResponse({"search_created": True})


@router.post("/delete_search/{search_id}")
def delete_search(
    search_id: int,
    db: Session = Depends(db_handler.get_db_connection),
):
    car_search = db.query(CarSearch).filter(CarSearch.id == search_id).first()
    if car_search is None:
        return JSONResponse(
            {"deleted": False, "reason": f"search {search_id} not found"},
            status_code=404,
        )

    db.delete(car_search)
    db.commit()
    return JSONResponse({"deleted": True, "search_id": search_id})


@router.get("/get_models/{manufacturer}", response_model=List[str])
def get_models(
    manufacturer: str,
    db: Session = Depends(db_handler.get_db_connection),
):
    models = (
        db.query(CarModel.model).filter(CarModel.manufacturer == manufacturer).all()
    )
    models = list(map(lambda el: el[0], models))
    return sorted(models)
