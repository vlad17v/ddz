"""Main of todo app
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from app.router import todo_router
from app.database import lifespan

app = FastAPI(
    lifespan=lifespan
)

@app.get("/")
async def main_page():
    return RedirectResponse("/todo/home", status_code=303)



app.include_router(todo_router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
