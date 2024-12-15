"""Main of todo app
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from app.flowers_router import flowers_router
from app.router import todo_router
from app.auth import auth_router
from app.utils import create_dirs

app = FastAPI()


@app.get("/")
async def main_page():
    return RedirectResponse("/todo/home", status_code=303)


@app.exception_handler(401)
async def my_401(_, __):
    return RedirectResponse("/todo/401", status_code=401)


app.include_router(todo_router)
app.include_router(auth_router)
app.include_router(flowers_router)

create_dirs()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/images", StaticFiles(directory="images"), name="images")
