from fastapi import APIRouter
from fastapi import Request
from fastapi import Form
from fastapi import status
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from java import Client

client_router = APIRouter(
    prefix="/client",
    tags=["Client"]
)

templates = Jinja2Templates(directory="app/templates")
client = Client()

@client_router.get("/flowers/", status_code=status.HTTP_200_OK)
async def get_flowers(request: Request):
    """Get all flowers"""
    flowers = client.get_all_flowers()
    client.server_stopped()
    return templates.TemplateResponse("flowers.html", {"request": request, "flowers": flowers})

@client_router.post("/add_flower/", status_code=status.HTTP_201_CREATED)
async def add_flower(request: Request, name: str = Form(...), color: str = Form(...), price: float = Form(...), quantity: int = Form(...)):
    """Add a new flower"""
    flower = {"name": name, "color": color, "price": price, "quantity": quantity, "id": 0}
    client.add_flower(flower)
    client.server_stopped()
    return RedirectResponse("/client/flowers/", status_code=status.HTTP_303_SEE_OTHER)

