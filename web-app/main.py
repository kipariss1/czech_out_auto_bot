from fastapi import FastAPI
from src import sqlite_db_handler

app = FastAPI()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, "0.0.0.0", port=8000)
