import os
from linecache import cache

import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Alignment
from fastapi import UploadFile
import random
import string
from loguru import logger

from app.models import Todo
from datetime import datetime

from app.schemas import TodoSource


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


async def load_image(image: UploadFile, random_filename: str):
    file_location = os.path.join('./images/', random_filename)
    with open(file_location, "wb") as file:
        file.write(await image.read())

def generate_random_filename(length=10):
    """Generate a random filename of specified length."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

async def delete_image(image_path: str):
    try:
        if os.path.exists("./images/"+image_path):
            os.remove("./images/"+image_path)
    except Exception as e:
        logger.error(f"Bad path: {e.decode()}")


