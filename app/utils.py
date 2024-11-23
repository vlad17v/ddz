import os

import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Alignment

from app.models import Todo
from datetime import datetime


def export_todos(todos: list[Todo]):
    if not os.path.exists("data"):
        os.mkdir("data")

    wb = Workbook()
    wb.remove(wb.active)
    ws = wb.create_sheet("todos", 0)

    headers = ["id", "title", "details", "completed", "tag", "created_at", "completed_at"]
    for index, header in enumerate(headers):
        ws.column_dimensions[f"{chr(index + 65)}"].width = len(header) + 5
    ws.append(headers)
    for cell in ws[1]:
        cell.alignment = Alignment(horizontal='center')

    for todo in todos:
        ws.append([todo.id,
                   todo.title,
                   todo.details,
                   "Выполнено" if todo.completed else "Не выполнено",
                   todo.tag,
                   todo.created_at,
                   todo.completed_at])

    wb.save("data/todos.xlsx")


def import_todos(file_path) -> list[Todo]:
    workbook = openpyxl.load_workbook(file_path)
    sheet = workbook.active

    todos = []

    for row in sheet.iter_rows(min_row=2, values_only=True):
        id, title, details, completed, tag, created_at, completed_at = row

        if not completed and completed_at is not None:
            print(f"Ошибка: Задача с ID {id} не завершена, но дата выполнения указана.")
            continue

        created_at = created_at if isinstance(created_at, datetime) else None
        completed_at = completed_at if isinstance(completed_at, datetime) else None

        todo = Todo()
        todo.id = id
        todo.title = title
        todo.details = details if details is not None else ""
        todo.completed = bool(completed)
        todo.tag = tag
        todo.created_at = created_at
        todo.completed_at = completed_at
        todos.append(todo)

    workbook.close()

    return todos
