from fastapi import APIRouter
from fastapi import Request
from fastapi import Form
from fastapi import status
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from app.pkg.java import Client

flowers_router = APIRouter(
    prefix="/flowers",
    tags=["Client"]
)

templates = Jinja2Templates(directory="app/templates")


@flowers_router.get("/", status_code=status.HTTP_200_OK)
async def get_flowers(request: Request):
    """Get all flowers"""
    client = Client()
    flowers = await client.get_all_flowers()
    await client.server_stopped()
    return templates.TemplateResponse("flowers.html", {"request": request, "flowers": flowers})


@flowers_router.post("/", status_code=status.HTTP_201_CREATED)
async def add_flower(request: Request, name: str = Form(...), color: str = Form(...), price: float = Form(...),
                     quantity: int = Form(...)):
    """Add a new flower"""
    flower = {"name": name, "color": color, "price": price, "quantity": quantity, "id": 0}
    client = Client()
    await client.add_flower(flower)
    await client.server_stopped()
    return RedirectResponse("/flowers/", status_code=status.HTTP_303_SEE_OTHER)
