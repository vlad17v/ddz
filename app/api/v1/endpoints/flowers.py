from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import Request
from fastapi import status
from fastapi.responses import RedirectResponse

from app.core.templates import templates
from app.dependencies import get_flower_service
from app.services.flower_service import FlowerService

router = APIRouter(prefix="/flowers", tags=["Flowers"])


@router.get("/", status_code=status.HTTP_200_OK)
async def get_flowers(request: Request, flower_service: FlowerService = Depends(get_flower_service)):
    flowers = await flower_service.get_all_flowers()
    return templates.TemplateResponse("flowers.html", {"request": request, "flowers": flowers})


@router.post("/", status_code=status.HTTP_201_CREATED)
async def add_flower(
    request: Request,
    name: str = Form(...),
    color: str = Form(...),
    price: float = Form(...),
    quantity: int = Form(...),
    flower_service: FlowerService = Depends(get_flower_service),
):
    await flower_service.add_flower({"name": name, "color": color, "price": price, "quantity": quantity, "id": 0})
    return RedirectResponse("/flowers/", status_code=status.HTTP_303_SEE_OTHER)
