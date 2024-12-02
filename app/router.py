import base64
import math
import io
from typing import Annotated

import squarify
import os
from datetime import datetime

import asyncio
import shutil
import matplotlib.pyplot as plt
import seaborn as sb
from loguru import logger
from fastapi import APIRouter
from fastapi import Request
from fastapi import File
from fastapi import UploadFile
from fastapi import Depends
from fastapi import status
from fastapi import HTTPException
from fastapi import Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from typing import Optional


from app.auth import get_current_active_user
from app.database import get_async_uow_session
from app.schemas import User
from app.schemas import Todo
from app.schemas import Tags
from app.schemas import TodoSource
from app.utils import export_todos
from app.utils import generate_random_filename
from app.utils import delete_image
from app.utils import load_image
from app.utils import import_todos
from app.utils import delete_image
from app.uow import UnitOfWork


todo_router = APIRouter(
    prefix="/todo",
    tags=["Todo"]
)

# pylint: disable=invalid-name
templates = Jinja2Templates(directory="app/templates")

logger = logger.opt(colors=True)


# pylint: enable=invalid-name

@todo_router.get("/home/", status_code=status.HTTP_200_OK)
async def get_home(request: Request):
    """Main page with todo list
    """
    logger.info("In home")

    return templates.TemplateResponse("index.html",
                                      {"request": request})


@todo_router.get("/401", status_code=status.HTTP_200_OK)
async def page_401(request: Request):
    """Main page with todo list
    """
    return templates.TemplateResponse("401.html",
                                      {"request": request})


@todo_router.get("/info-tasks/", status_code=status.HTTP_200_OK)
async def get_home(request: Request):
    """Main page with todo list
    """

    return templates.TemplateResponse("info-tasks.html",
                                      {"request": request})


@todo_router.get("/list/", status_code=status.HTTP_200_OK)
async def get_todos(request: Request, uow_session: UnitOfWork = Depends(get_async_uow_session),
                    limit: int = 10, skip: int = 0, creation_date_start: str = None, creation_date_end: str = None,
                    tag: Tags = None):
    creation_date_start = datetime.strptime(creation_date_start, "%Y-%m-%d") if creation_date_start else None
    creation_date_end = datetime.strptime(creation_date_end, "%Y-%m-%d") if creation_date_end else None

    count = await uow_session.todo.get_count_todos(creation_date_start, creation_date_end, tag)
    pages = math.ceil(count / limit)

    if skip > pages:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such page")
    if not pages:
        pages = 1

    todos = await uow_session.todo.get_todos(limit, skip, creation_date_start, creation_date_end, tag)

    return templates.TemplateResponse("todos.html",
                                      {"request": request, "todos": todos, "page": skip, "pages": pages,
                                       "limit": limit, "creation_date_start": creation_date_start,
                                       "creation_date_end": creation_date_end, "tag": tag})


@todo_router.post("/add/", status_code=status.HTTP_201_CREATED)
async def add_todo(
        title: str = Form(...),
        details: str = Form(...),
        tag: Tags = Form(...),
        image: UploadFile = File(None),
        source: str = Form(...),
        uow_session: UnitOfWork = Depends(get_async_uow_session)
):
    """Add new todo"""
    logger.info(f"Creating todo: title={title}, details={details}, tag={tag}")

    random_filename = None
    if image and image.filename:
        random_filename = generate_random_filename() + "." + image.filename.split('.')[-1]
        try:
            await load_image(image, random_filename)
            logger.info(f"Image uploaded successfully: {random_filename}")
        except Exception as e:
            logger.error(f"Error uploading image: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Image upload failed", source=source)

    todo = Todo(title=title, details=details, tag=tag, image_path=random_filename, source=source)
    await uow_session.todo.add_todo(todo.model_dump())

    logger.info("Todo added successfully")

    return JSONResponse(content={
        "status": "success",
        "details": "Todo added"
    })


@todo_router.get("/edit/{todo_id}/", status_code=status.HTTP_200_OK)
async def get_todo(
    request: Request,
    todo_id: int,
    limit: int = 10,
    skip: int = 0,
    uow_session: UnitOfWork = Depends(get_async_uow_session)
):
    """Get todo"""
    todo = await uow_session.todo.get_todo(todo_id)
    if not todo:
        logger.warning(f"Todo not found: {todo_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Not found todo by this id: {todo_id}"
        )

    logger.info(f"Getting todo: {todo}")
    return templates.TemplateResponse("edit.html",
                                      {"request": request, "todo": todo, "tags": Tags, "limit": limit, "skip": skip})


@todo_router.put("/edit/{todo_id}/", status_code=status.HTTP_200_OK)
async def edit_todo(todo_id: int,
                    title: str = Form(None),
                    details: str = Form(None),
                    completed: bool = Form(False),
                    tag: Tags = Form(None),
                    created_at: datetime = Form(None),
                    image_path: str = Form(None),
                    image: UploadFile = File(None),
                    uow_session: UnitOfWork = Depends(get_async_uow_session)
):
    """Edit todo
    """
    todo = await uow_session.todo.get_todo(todo_id)

    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Not found todo by this id: {todo_id}"
        )
    print(image_path)
    random_filename = None
    if image and image.filename:
        random_filename = generate_random_filename() + "." + image.filename.split('.')[-1]
        todo_change = Todo(title=title, details=details, completed=completed, tag=tag, created_at=created_at,
                           image_path=random_filename)
        await load_image(image, random_filename)
        if todo.image_path is not None:
            await delete_image(todo.image_path)
    else:
        todo_change = Todo(title=title, details=details, completed=completed, tag=tag, created_at=created_at, image_path=image_path)



    logger.info(f"Editting todo: {todo}")

    if todo_change.completed:
        todo_change.completed_at = datetime.utcnow()

    todo_change.source = todo.source

    await uow_session.todo.update_todo(todo_id, todo_change.model_dump())
    return {
        "status": "success",
        "details": "Todo edited"
    }


@todo_router.delete("/delete/{todo_id}/", status_code=status.HTTP_200_OK)
async def delete_todo(todo_id: int, limit: int = 10, skip: int = 0,
                      uow_session: UnitOfWork = Depends(get_async_uow_session)):
    """Delete todo
    """
    todo = await uow_session.todo.get_todo(todo_id)

    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Not found todo by this id: {todo_id}"
        )

    logger.info(f"Deleting todo: {todo}")
    if todo.image_path is not None:
        await delete_image(todo.image_path)

    await uow_session.todo.delete_todo(todo_id)
    return {
        "status": "success",
        "details": "Todo deleted",
        "limit": limit,
        "skip": skip
    }


@todo_router.delete("/delete/", status_code=status.HTTP_200_OK)
async def delete_todos(uow_session: UnitOfWork = Depends(get_async_uow_session),
                       limit: int = 10, skip: int = 0, start: int = 0, end: int = 0):
    count = await uow_session.todo.get_count_todos()
    pages = math.ceil(count / limit)

    if skip > pages or start > end:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect range")


    await uow_session.todo.delete_todos(skip, limit, start, end)
    return {
        "status": "success",
        "details": "Todos deleted",
        "limit": limit,
        "skip": skip
    }


@todo_router.get("/visualize/", status_code=status.HTTP_200_OK)
async def visualize_todos(request: Request, uow_session: UnitOfWork = Depends(get_async_uow_session)):
    """Visualize todos as a treemap by tags
    """
    todos = await uow_session.todo.get_todos(limit=1000, skip=0)

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
        squarify.plot(sizes=list(tag_counts.values()), label=list(tag_counts.keys()), pad=0.2,
                      text_kwargs={'fontsize': 10, 'color': 'white'},
                      color=sb.color_palette("rocket", len(tag_counts)))
        plt.axis('off')

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)

    image_url = f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"
    return templates.TemplateResponse("visualization.html", {"request": request, "image_url": image_url})


@todo_router.get("/generate/", status_code=status.HTTP_200_OK)
async def show_generate(request: Request):
    return templates.TemplateResponse("generate.html", {"request": request})

@todo_router.post("/generate/", status_code=status.HTTP_200_OK)
async def generate_todos(count: int = Form(20)):
    """Generate a number of todos by calling a bash script."""
    logger.info(f"Generating {count} todos")
    script_directory = os.path.dirname(__file__)
    script_path = os.path.join(script_directory, "../scripts/generate.sh")

    try:
        process = await asyncio.create_subprocess_exec(
            "bash", script_path, str(count),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            logger.error(f"Error during execution: {stderr.decode()}")
            raise HTTPException(status_code=500, detail=f"Error during execution: {stderr.decode()}")

        logger.info("Todos generated successfully")
        return RedirectResponse(url="/todo/home", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while generating todos")


@todo_router.get("/export/", status_code=status.HTTP_200_OK)
async def visualize_todos(request: Request):
    """Page export and import todos from excel file
    """
    return templates.TemplateResponse("export.html",
                                      {"request": request})


@todo_router.post("/import")
async def import_file(current_user: Annotated[User, Depends(get_current_active_user)], file: UploadFile = File(...), uow_session: UnitOfWork = Depends(get_async_uow_session)):
    with open(file.filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    todos = import_todos(file.filename)

    for todo in todos:
        await uow_session.todo.add_todo_object(todo)

    return RedirectResponse("/todo/home", status_code=status.HTTP_303_SEE_OTHER)


@todo_router.post("/export/")
async def export_data(uow_session: UnitOfWork = Depends(get_async_uow_session)):
    todos = await uow_session.todo.get_all_todos()

    export_todos(todos)

    return FileResponse("data/todos.xlsx",
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")