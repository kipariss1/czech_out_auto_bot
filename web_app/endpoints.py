from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
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


@router.get("/", response_class=HTMLResponse)
def main_view(request: requests.Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/create_search", response_class=HTMLResponse)
def create_search_view(
    request: requests.Request,
    db: Session = Depends(sqlite_db_handler.get_db_connection),
):
    unique_car_manufacturers = db.query(distinct(CarModel.manufacturer)).all()
    unique_car_manufacturers = list(map(lambda el: el[0], unique_car_manufacturers))
    render_dict = {"request": request, "car_manufacturers": unique_car_manufacturers}
    return templates.TemplateResponse("create_search.html", render_dict)


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
    if len(cars) != 1:
        raise Exception("The car name is not found or ambiguous")
    # TODO: find a way to fetch user from tg to web app and to backend
    # TODO: finish the creation of the new search
    attributes = []
    new_search = CarSearch(
        user_id=1,
        car_model_id=cars[0].id,
        psc_code=request.psc_code,
        psc_km_range=request.psc_km_range,
    )


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
