import base64
import io
import math
from datetime import datetime
from datetime import timedelta

import matplotlib.pyplot as plt
import seaborn as sb
import squarify
from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import Form
from fastapi import HTTPException
from fastapi import Request
from fastapi import UploadFile
from fastapi import status
from fastapi.responses import FileResponse
from fastapi.responses import RedirectResponse

from app.core.templates import templates
from app.dependencies import get_current_active_user
from app.dependencies import get_tag_service
from app.dependencies import get_todo_service
from app.models.schemas import TodoSource
from app.services.tag_service import TagService
from app.services.todo_service import TodoService
from app.services.todo_service import _parse_tags

router = APIRouter(prefix="/todo", tags=["Todo"])


def parse_date(value: str | None, *, end_of_day: bool = False) -> datetime | None:
    if not value:
        return None
    parsed = datetime.strptime(value, "%Y-%m-%d")
    if end_of_day:
        return parsed + timedelta(days=1) - timedelta(microseconds=1)
    return parsed


@router.get("/home/", status_code=status.HTTP_200_OK)
async def get_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/401", status_code=status.HTTP_200_OK)
async def page_401(request: Request):
    return templates.TemplateResponse("401.html", {"request": request})


@router.get("/info-tasks/", status_code=status.HTTP_200_OK)
async def get_info(request: Request):
    return templates.TemplateResponse("info-tasks.html", {"request": request})


@router.get("/list/", status_code=status.HTTP_200_OK)
async def get_todos(
    request: Request,
    todo_service: TodoService = Depends(get_todo_service),
    limit: int = 10,
    skip: int = 0,
    creation_date_start: str | None = None,
    creation_date_end: str | None = None,
    tag: str | None = None,
    query: str | None = None,
):
    start_date = parse_date(creation_date_start)
    end_date = parse_date(creation_date_end, end_of_day=True)
    todos, count = await todo_service.list_todos(
        limit=limit,
        skip=skip,
        creation_date_start=start_date,
        creation_date_end=end_date,
        tag=tag,
        query=query,
    )
    pages = math.ceil(count / limit) if count else 1
    if skip >= pages and count:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such page")
    return templates.TemplateResponse(
        "todos.html",
        {
            "request": request,
            "todos": todos,
            "page": skip,
            "pages": pages,
            "limit": limit,
            "creation_date_start": start_date,
            "creation_date_end": end_date,
            "tag": tag,
            "query": query or "",
        },
    )


@router.post("/add/", status_code=status.HTTP_201_CREATED)
async def add_todo(
    title: str = Form(...),
    details: str = Form(...),
    tags: str = Form(""),
    image: UploadFile | None = File(None),
    source: TodoSource = Form(...),
    count_todos: str | None = Form(None),
    current_user=Depends(get_current_active_user),
    todo_service: TodoService = Depends(get_todo_service),
):
    normalized_count = int(count_todos) if count_todos else 1
    await todo_service.create_todo(
        title=title,
        details=details,
        tags=_parse_tags(tags),
        source=source,
        count_todos=normalized_count,
        image=image,
    )
    return {"status": "success", "details": "Todo added"}


@router.get("/edit/{todo_id}/", status_code=status.HTTP_200_OK)
async def get_todo(
    request: Request,
    todo_id: int,
    limit: int = 10,
    skip: int = 0,
    todo_service: TodoService = Depends(get_todo_service),
):
    todo = await todo_service.get_todo(todo_id)
    images = await todo_service.get_all_image_paths()
    return templates.TemplateResponse(
        "edit.html",
        {"request": request, "todo": todo, "limit": limit, "skip": skip, "images": images},
    )


@router.put("/edit/{todo_id}/", status_code=status.HTTP_200_OK)
async def edit_todo(
    todo_id: int,
    title: str = Form(...),
    details: str = Form(...),
    completed: bool = Form(False),
    tags: str = Form(""),
    created_at: datetime | None = Form(None),
    image_path: str | None = Form(None),
    existing_image: str | None = Form(None),
    image: UploadFile | None = File(None),
    attachment: UploadFile | None = File(None),
    todo_service: TodoService = Depends(get_todo_service),
):
    await todo_service.update_todo(
        todo_id=todo_id,
        title=title,
        details=details,
        completed=completed,
        tags=_parse_tags(tags),
        created_at=created_at,
        image_path=image_path,
        existing_image=existing_image,
        image=image,
        attachment=attachment,
    )
    return {"status": "success", "details": "Todo edited"}


@router.delete("/delete/{todo_id}/", status_code=status.HTTP_200_OK)
async def delete_todo(
    todo_id: int,
    limit: int = 10,
    skip: int = 0,
    todo_service: TodoService = Depends(get_todo_service),
):
    await todo_service.delete_todo(todo_id)
    return {"status": "success", "details": "Todo deleted", "limit": limit, "skip": skip}


@router.delete("/delete/", status_code=status.HTTP_200_OK)
async def delete_todos(
    todo_service: TodoService = Depends(get_todo_service),
    limit: int = 10,
    skip: int = 0,
    start: int = 0,
    end: int = 0,
):
    await todo_service.delete_todos(skip=skip, limit=limit, start=start, end=end)
    return {"status": "success", "details": "Todos deleted", "limit": limit, "skip": skip}


@router.get("/visualize/", status_code=status.HTTP_200_OK)
async def visualize_todos(request: Request, todo_service: TodoService = Depends(get_todo_service)):
    todos, _ = await todo_service.list_todos(
        limit=1000,
        skip=0,
        creation_date_start=None,
        creation_date_end=None,
        tag=None,
        query=None,
    )
    tag_counts: dict[str, int] = {}
    for todo in todos:
        for tag in todo.tags:
            tag_counts[tag.name] = tag_counts.get(tag.name, 0) + 1

    if not tag_counts:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No todos available", ha="center", va="center", fontsize=18)
        plt.axis("off")
    else:
        fig, ax = plt.subplots()
        squarify.plot(
            sizes=list(tag_counts.values()),
            label=list(tag_counts.keys()),
            pad=0.2,
            text_kwargs={"fontsize": 10, "color": "white"},
            color=sb.color_palette("rocket", len(tag_counts)),
        )
        plt.axis("off")

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close(fig)
    image_url = f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"
    return templates.TemplateResponse(
        "visualization.html",
        {
            "request": request,
            "image_url": image_url,
            "tag_counts": tag_counts,
        },
    )


@router.get("/top-words/", status_code=status.HTTP_200_OK)
async def get_top_words_page(request: Request, todo_service: TodoService = Depends(get_todo_service)):
    top_words = await todo_service.get_top_words(limit=10)
    return templates.TemplateResponse(
        "top-words.html",
        {
            "request": request,
            "top_words": top_words,
        },
    )


@router.get("/generate/", status_code=status.HTTP_200_OK)
async def show_generate(request: Request):
    return templates.TemplateResponse("generate.html", {"request": request})


@router.post("/generate/", status_code=status.HTTP_200_OK)
async def generate_todos(count: int = Form(20), todo_service: TodoService = Depends(get_todo_service)):
    return {"status": "success", "details": await todo_service.generate_todos_via_script(count)}


@router.get("/export/", status_code=status.HTTP_200_OK)
async def show_export(request: Request):
    return templates.TemplateResponse("export.html", {"request": request})


@router.post("/export/")
async def export_data(include_id: bool = Form(False), todo_service: TodoService = Depends(get_todo_service)):
    export_path = await todo_service.export_all(include_id)
    return FileResponse(
        export_path,
        filename=datetime.now().strftime("%Y_%m_%d_%H_%M_%S") + ".xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.post("/import/")
async def import_file(
    file: UploadFile = File(...),
    current_user=Depends(get_current_active_user),
    todo_service: TodoService = Depends(get_todo_service),
):
    await todo_service.import_from_file(file)
    return RedirectResponse("/todo/home", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/import-log/")
async def import_log(request: Request, todo_service: TodoService = Depends(get_todo_service)):
    files = await todo_service.get_import_logs()
    return templates.TemplateResponse("import-log.html", {"request": request, "files": files})


@router.get("/import-log/{filename}")
async def get_import_log(filename: str, todo_service: TodoService = Depends(get_todo_service)):
    file_path = todo_service.get_import_log_path(filename)
    if not file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.get("/import-issues/", status_code=status.HTTP_200_OK)
async def get_import_issues(request: Request):
    return templates.TemplateResponse("issues.html", {"request": request})


@router.post("/import-issues/")
async def import_issues(
    url: str = Form(...),
    token: str = Form(...),
    todo_service: TodoService = Depends(get_todo_service),
):
    await todo_service.import_issues(url, token)
    return {"status": "success", "details": "imported successfully"}


@router.get("/shuffle-tag/", status_code=status.HTTP_200_OK)
async def shuffle_tag(
    todo_service: TodoService = Depends(get_todo_service),
    tag_service: TagService = Depends(get_tag_service),
):
    all_tags = await tag_service.get_all_tags()
    await todo_service.shuffle_tags(all_tags)
    return RedirectResponse("/todo/visualize/", status_code=status.HTTP_303_SEE_OTHER)
