from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from src import sqlite_db_handler

app = FastAPI()

app.mount("/static", StaticFiles(directory="src/web-app/static"), name="static")
templates = Jinja2Templates(directory="src/web-app/templates")


@app.get("/", response_class=HTMLResponse)
def main_view(request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/create_search", response_class=HTMLResponse)
def create_search_view(request):
    return templates.TemplateResponse("create_search.html", {"request": request})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, "0.0.0.0", port=8000)
