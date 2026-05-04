from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import status

from app.dependencies import get_tag_service
from app.services.tag_service import TagService

router = APIRouter(prefix="/tags", tags=["Tags"])


@router.get("/", status_code=status.HTTP_200_OK)
async def get_tags(tag_service: TagService = Depends(get_tag_service)):
    tags = await tag_service.get_all_tags()
    return [{"id": t.id, "name": t.name} for t in tags]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_tag(
    name: str = Form(...),
    tag_service: TagService = Depends(get_tag_service),
):
    tag = await tag_service.create_tag(name)
    return {"id": tag.id, "name": tag.name}


@router.delete("/{tag_id}/", status_code=status.HTTP_200_OK)
async def delete_tag(tag_id: int, tag_service: TagService = Depends(get_tag_service)):
    await tag_service.delete_tag(tag_id)
    return {"status": "success"}


@router.get("/suggest/", status_code=status.HTTP_200_OK)
async def suggest_tags(
    q: str = "",
    tag_service: TagService = Depends(get_tag_service),
):
    return await tag_service.suggest_tags(q)
