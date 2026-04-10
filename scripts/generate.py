#!/usr/bin/env python3
import os
import random
import sys

import httpx


DETAILS = [
    "Купить молоко",
    "Починить кран",
    "Сделать домашку",
    "Пойти на пробежку",
    "Позвонить другу",
    "Записаться на курсы",
    "Сделать уборку",
    "Сходить в магазин",
    "Приготовить ужин",
    "Почитать книгу",
    "Посмотреть фильм",
    "Написать статью",
    "Выучить новый язык",
    "Собрать документы",
    "Погулять с собакой",
    "Сделать фотографии",
    "Составить план на неделю",
    "Попробовать новый рецепт",
    "Подготовить презентацию",
    "Отдохнуть",
]

TAGS = ["Учёба", "Личное", "Планы"]
BASE_URL = os.getenv("TODO_BASE_URL", "http://web:8000")
USERNAME = "generator"
PASSWORD = "generator"


def ensure_auth(client: httpx.Client) -> None:
    register_response = client.post(
        f"{BASE_URL}/auth/register",
        data={"username": USERNAME, "password": PASSWORD},
    )
    if register_response.status_code not in {200, 303, 400}:
        raise RuntimeError(f"Register failed: {register_response.status_code} {register_response.text}")

    login_response = client.post(
        f"{BASE_URL}/auth/token",
        data={"username": USERNAME, "password": PASSWORD},
        follow_redirects=False,
    )
    if login_response.status_code not in {302, 303}:
        raise RuntimeError(f"Login failed: {login_response.status_code} {login_response.text}")


def create_todos(client: httpx.Client, count: int) -> None:
    for index in range(1, count + 1):
        response = client.post(
            f"{BASE_URL}/todo/add/",
            data={
                "title": f"Задача {index}",
                "details": random.choice(DETAILS),
                "tag": random.choice(TAGS),
                "source": "Сгенерированная",
            },
        )
        if response.status_code != 201:
            raise RuntimeError(f"Todo create failed: {response.status_code} {response.text}")


def main() -> int:
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    with httpx.Client(timeout=20.0) as client:
        ensure_auth(client)
        create_todos(client, count)
    print(f"Generated {count} todos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
