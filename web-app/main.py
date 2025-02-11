from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from src import sqlite_db_handler

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def main_view():
    pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, "0.0.0.0", port=8000)
