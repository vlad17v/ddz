import math
import io
import squarify

from loguru import logger
from fastapi import APIRouter
from fastapi import Request
from fastapi import Depends
from fastapi import status
from fastapi import HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import matplotlib.pyplot as plt
import seaborn as sb

from app.database import get_async_session
from app.repository import TodoRepository
from app.schemas import Todo
from app.schemas import Tags


todo_router = APIRouter(
    prefix="/todo",
    tags=["Todo"]
)


# pylint: disable=invalid-name
templates = Jinja2Templates(directory="app/templates")

logger = logger.opt(colors=True)
# pylint: enable=invalid-name

@todo_router.get("/home/", status_code=status.HTTP_200_OK)
async def get_home(request: Request, session: AsyncSession = Depends(get_async_session),
                   limit: int = 10, skip: int = 0):
    """Main page with todo list
    """
    logger.info("In home")

    todo_repo = TodoRepository(session)
    count = await todo_repo.get_count_todos()
    pages = math.ceil(count / limit)

    if skip > pages:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such page")

    todos = await todo_repo.get_todos(limit, skip)

    return templates.TemplateResponse("index.html",
        {"request": request, "todos": todos, "page": skip, "pages": pages, "limit": limit})

@todo_router.post("/add/", status_code=status.HTTP_201_CREATED)
async def add_todo(todo: Todo, session: AsyncSession = Depends(get_async_session)):
    """Add new todo
    """
    logger.info(f"Creating todo: {todo}")

    todo_repo = TodoRepository(session)
    await todo_repo.add_todo(todo.model_dump())
    return {
        "status": "success",
        "details": "Todo added"
    }

@todo_router.get("/edit/{todo_id}/", status_code=status.HTTP_200_OK)
async def get_todo(request: Request, todo_id: int, session: AsyncSession = Depends(get_async_session)):
    """Get todo
    """
    todo_repo = TodoRepository(session)
    todo = await todo_repo.get_todo(todo_id)

    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Not found todo by this id: {todo_id}"
        )

    logger.info(f"Getting todo: {todo}")
    return templates.TemplateResponse("edit.html", {"request": request, "todo": todo, "tags": Tags})

@todo_router.put("/edit/{todo_id}/", status_code=status.HTTP_200_OK)
async def edit_todo(todo_id: int, todo_change: Todo,
                    session: AsyncSession = Depends(get_async_session)):
    """Edit todo
    """
    todo_repo = TodoRepository(session)
    todo = await todo_repo.get_todo(todo_id)

    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Not found todo by this id: {todo_id}"
        )

    logger.info(f"Editting todo: {todo}")
    await todo_repo.update_todo(todo_id, todo_change.model_dump())
    return {
        "status": "success",
        "details": "Todo edited"
    }

@todo_router.delete("/delete/{todo_id}/", status_code=status.HTTP_200_OK)
async def delete_todo(todo_id: int, session: AsyncSession = Depends(get_async_session)):
    """Delete todo
    """
    todo_repo = TodoRepository(session)
    todo = await todo_repo.get_todo(todo_id)

    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Not found todo by this id: {todo_id}"
        )

    logger.info(f"Deleting todo: {todo}")
    await todo_repo.delete_todo(todo_id)
    return {
        "status": "success",
        "details": "Todo deleted"
    }

@todo_router.get("/visualize/", status_code=status.HTTP_200_OK)
async def visualize_todos(session: AsyncSession = Depends(get_async_session)):
    """Visualize todos as a treemap by tags
    """
    todo_repo = TodoRepository(session)
    todos = await todo_repo.get_todos(limit=1000, skip=0)

    tag_counts = {tag.value: 0 for tag in Tags}
    for todo in todos:
        tag_counts[todo.tag] += 1

    tag_counts = {tag: count for tag, count in tag_counts.items() if count > 0}

    if not tag_counts:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No todos available", ha="center", va="center", fontsize=18)
        plt.axis('off')
    else:
        fig, ax = plt.subplots()
        squarify.plot(sizes=list(tag_counts.values()), label=list(tag_counts.keys()),  pad = 0.2, text_kwargs = {'fontsize': 10, 'color': 'white'},
              color = sb.color_palette("rocket", len(tag_counts)))
        plt.axis('off')

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")