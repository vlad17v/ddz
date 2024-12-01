import os

import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Alignment

from app.models import Todo
from datetime import datetime

from app.schemas import TodoSource

from fastapi.security import OAuth2
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi import Request
from fastapi.security.utils import get_authorization_scheme_param
from fastapi import HTTPException
from fastapi import status
from typing import Optional
from typing import Dict



def export_todos(todos: list[Todo]):
    if not os.path.exists("data"):
        os.mkdir("data")

    wb = Workbook()
    wb.remove(wb.active)
    ws = wb.create_sheet("todos", 0)

    headers = ["title", "details", "completed", "tag", "created_at", "completed_at"]
    for index, header in enumerate(headers):
        ws.column_dimensions[f"{chr(index + 65)}"].width = len(header) + 5
    ws.append(headers)
    for cell in ws[1]:
        cell.alignment = Alignment(horizontal='center')

    for todo in todos:
        ws.append([
            todo.title,
            todo.details,
            "Выполнено" if todo.completed else "Не выполнено",
            todo.tag,
            todo.created_at.strftime("%Y-%m-%d %H:%M:%S") if todo.created_at is not None else "",
            todo.completed_at.strftime("%Y-%m-%d %H:%M:%S") if todo.completed_at is not None else ""])

    wb.save("data/todos.xlsx")


def import_todos(file_path) -> list[Todo]:
    workbook = openpyxl.load_workbook(file_path)
    sheet = workbook.active

    todos = []

    for row in sheet.iter_rows(min_row=2, values_only=True):
        title, details, completed, tag, created_at, completed_at = row

        if not completed and completed_at is not None:
            print(f"Ошибка: Задача с ID {id} не завершена, но дата выполнения указана.")
            continue

        created_at = created_at if isinstance(created_at, datetime) else None
        completed_at = completed_at if isinstance(completed_at, datetime) else None

        todo = Todo()
        todo.title = title
        todo.details = details if details is not None else ""
        todo.completed = True if completed == "Выполнено" else False
        todo.tag = tag
        todo.created_at = created_at
        todo.completed_at = completed_at
        todo.source = TodoSource.imported
        todos.append(todo)

    workbook.close()

    return todos

class OAuth2PasswordBearerWithCookie(OAuth2):
    def __init__(
            self,
            tokenUrl: str,
            scheme_name: Optional[str] = None,
            scopes: Optional[Dict[str, str]] = None,
            auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        authorization: str = request.cookies.get("access_token")  # changed to accept access token from httpOnly Cookie

        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        return param
