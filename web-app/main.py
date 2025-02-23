from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
from sqlalchemy import distinct
from src import sqlite_db_handler
from src.models.models import CarModel

app = FastAPI()

app.mount("/static", StaticFiles(directory="web-app/static"), name="static")
templates = Jinja2Templates(directory="web-app/templates")


@app.get("/", response_class=HTMLResponse)
def main_view(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/create_search", response_class=HTMLResponse)
def create_search_view(request: Request):
    db = sqlite_db_handler.get_db_connection()
    unique_car_manufacturers = db.query(distinct(CarModel.manufacturer)).all()
    unique_car_manufacturers = list(map(lambda el: el[0], unique_car_manufacturers))
    render_dict = {"request": request, "car_manufacturers": unique_car_manufacturers}
    return templates.TemplateResponse("create_search.html", render_dict)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app=app, host="0.0.0.0", port=8000)
