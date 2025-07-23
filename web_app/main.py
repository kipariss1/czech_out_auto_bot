import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from web_app.endpoints import router


app = FastAPI()
app.include_router(router)
BASE_DIR = Path(os.path.abspath(__file__)).parent
app.mount("/static", StaticFiles(directory= BASE_DIR / "static"), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app=app, host="0.0.0.0", port=8000)
