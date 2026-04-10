# ToDo App

## Запуск

```bash
docker compose -f docker-compose.yml build

docker compose -f docker-compose.yml up
```

## Тесты

```bash
docker compose -f docker-compose-test.yml build

docker compose -f docker-compose-test.yml up

docker compose exec test /bin/bash
```

```bash
pytest -v tests/test_todos.py # запуск всех тестов

pytest -v tests/test_todos.py::test_add_todo_success # запуск конкретного теста
```

## Генерация данных

```bash
docker build -f Dockerfile_generate -t todo-generator .
docker run --rm --network python-ddz_app-network todo-generator 20
```

Генератор написан на Python и создает задачи через HTTP-ручку `/todo/add/`.
