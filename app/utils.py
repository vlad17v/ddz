import os

from openpyxl import Workbook
from openpyxl.styles import Alignment

from app.models import Todo

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
