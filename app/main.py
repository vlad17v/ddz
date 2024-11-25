"""Main of todo app
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from app.router import todo_router

app = FastAPI()

@app.get("/")
async def main_page():
    return RedirectResponse("/todo/home", status_code=303)


app.include_router(todo_router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
