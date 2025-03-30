from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from starlette import requests
from sqlalchemy import distinct, and_
from sqlalchemy.orm import Session
from src import sqlite_db_handler
from src.models.models import CarModel
from fastapi.templating import Jinja2Templates
from typing import List
from src.models.models import CarSearchCreate, CarSearch


router = APIRouter()
templates = Jinja2Templates(directory="web_app/templates")


@router.get("/")
def main_view(request: Request, enc_user_id: str = None):
    response = templates.TemplateResponse("index.html", {"request": request})
    response.set_cookie(
        key="enc_user_id", value=enc_user_id, samesite="strict", max_age=3600
    )
    return response


@router.get("/create_search", response_class=HTMLResponse)
def create_search_view(
    request: requests.Request,
    db: Session = Depends(sqlite_db_handler.get_db_connection),
):
    unique_car_manufacturers = db.query(distinct(CarModel.manufacturer)).all()
    unique_car_manufacturers = list(map(lambda el: el[0], unique_car_manufacturers))
    render_dict = {"request": request, "car_manufacturers": unique_car_manufacturers}
    return templates.TemplateResponse("create_search.html", render_dict)


def _construct_attributes(request: dict) -> dict:
    attributes_keys = [
        "input_year_range_from",
        "input_year_range_to",
        "input_mileage_range_from",
        "input_mileage_range_to",
        "input_price_range_from",
        "input_price_range_to",
    ]
    attributes = {
        k: v
        for k, v in request.items()
        if k in attributes_keys or ("attributes_" in k and len(v) > 0)
    }
    return attributes


@router.post("/create_search", response_class=HTMLResponse)
def post_create_search_view(
    request: CarSearchCreate,
    db: Session = Depends(sqlite_db_handler.get_db_connection),
):
    cars = db.query(CarModel).filter(
        and_(
            CarModel.manufacturer == request.manufacturer,
            CarModel.model == request.model,
        )
    )
    if len(list(cars)) != 1:
        raise Exception("The car name is not found or ambiguous")
    # TODO: decrypt the enc_user_id here
    # TODO: check if the same search exists
    new_search = CarSearch(
        user_id=request.enc_user_id,
        car_model_id=cars[0].id,
        psc_code=request.psc_code,
        psc_km_range=request.psc_km_range,
        attributes=_construct_attributes(dict(request)),
    )
    db.add(new_search)
    db.commit()


@router.get("/get_models/{manufacturer}", response_model=List[str])
def get_models(
    manufacturer: str,
    db: Session = Depends(sqlite_db_handler.get_db_connection),
):
    models = (
        db.query(CarModel.model).filter(CarModel.manufacturer == manufacturer).all()
    )
    models = list(map(lambda el: el[0], models))
    return sorted(models)


@router.get("/get_searches/{enc_user_id}", response_class=JSONResponse)
def get_searches(
    enc_user_id: str, db: Session = Depends(sqlite_db_handler.get_db_connection)
):
    # TODO: decrypt user id and get searches from databases
    return JSONResponse({})
