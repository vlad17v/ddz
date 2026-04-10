from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.core.elasticsearch import lifespan
from app.utils import create_dirs

create_dirs()

app = FastAPI(lifespan=lifespan)


@app.get("/")
async def main_page():
    return RedirectResponse("/todo/home", status_code=303)


@app.exception_handler(401)
async def my_401(_, __):
    return RedirectResponse("/todo/401", status_code=401)


app.include_router(api_router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/images", StaticFiles(directory="images"), name="images")
