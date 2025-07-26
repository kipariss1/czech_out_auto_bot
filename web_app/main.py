import ssl
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from web_app.endpoints import router
from web_app import BASE_DIR


app = FastAPI()
app.include_router(router)
app.mount("/static", StaticFiles(directory= BASE_DIR / "static"), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app=app, 
        host="0.0.0.0", 
        port=8000, 
        ssl_keyfile=BASE_DIR.parent / "certs" / "ssl.key", 
        ssl_certfile=BASE_DIR.parent / "certs" / "ssl.crt"
        )
