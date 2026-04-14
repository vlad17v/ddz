#!/usr/bin/env python3
from datetime import datetime
import os
import random
import sys
from uuid import uuid4

import httpx


TITLE_PREFIXES = [
    "Проверить",
    "Подготовить",
    "Согласовать",
    "Собрать",
    "Найти",
    "Описать",
    "Изучить",
    "Запланировать",
]

TITLE_SUBJECTS = [
    "красный отчет",
    "учебный проект",
    "личный план",
    "новую задачу",
    "список покупок",
    "тест поиска",
    "рабочий документ",
    "план на неделю",
]

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

TEST_CASES = [
    {
        "title": "Проверка стоп слов",
        "details": "И в на под для по от у около задачи есть русские стоп слова для проверки анализа",
        "tag": "Учёба",
    },
    {
        "title": "Проверка имён группы",
        "details": "Дима Артем Сергей должны проверяться как пользовательские стоп слова анализатора",
        "tag": "Личное",
    },
    {
        "title": "Проверка грифа секретности",
        "details": "Совершенно секретно и конфиденциально должны заменяться при анализе документа",
        "tag": "Планы",
    },
    {
        "title": "Проверка служебного пользования",
        "details": "Для служебного пользования красная задача для поиска по грифам секретности",
        "tag": "Учёба",
    },
    {
        "title": "Проверка морфологии",
        "details": "красный документ и красная задача нужны для проверки нестрогого соответствия",
        "tag": "Планы",
    },
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


def build_run_id() -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"{timestamp}-{uuid4().hex[:6]}"


def build_random_title(run_id: str, index: int) -> str:
    return f"{random.choice(TITLE_PREFIXES)} {random.choice(TITLE_SUBJECTS)} [{run_id}-{index}]"


def build_payload(index: int, run_id: str) -> dict[str, str]:
    if index < len(TEST_CASES):
        payload = TEST_CASES[index].copy()
        payload["title"] = f"{payload['title']} [{run_id}-{index + 1}]"
    else:
        payload = {
            "title": build_random_title(run_id, index + 1),
            "details": random.choice(DETAILS),
            "tag": random.choice(TAGS),
        }
    payload["source"] = "Сгенерированная"
    return payload


def create_todos(client: httpx.Client, count: int) -> None:
    run_id = build_run_id()
    for index in range(count):
        response = client.post(
            f"{BASE_URL}/todo/add/",
            data=build_payload(index, run_id),
        )
        if response.status_code != 201:
            raise RuntimeError(f"Todo create failed: {response.status_code} {response.text}")
    print(f"Generated {count} todos with run_id={run_id}")


def main() -> int:
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    with httpx.Client(timeout=20.0) as client:
        ensure_auth(client)
        create_todos(client, count)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
