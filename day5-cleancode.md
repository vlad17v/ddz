# Структурирование FastAPI + Elasticsearch приложения

Чтобы создать хорошо структурированное FastAPI приложение с Elasticsearch, которое разделяет API логику от бизнес-логики и легко тестируется, рекомендую следующую структуру:

```
my_app/
│
├── app/                      # Основное приложение
│   ├── api/                  # FastAPI роутеры и эндпоинты
│   │   ├── v1/               # Версия API
│   │   │   ├── endpoints/    # Эндпоинты по модулям
│   │   │   │   ├── items.py
│   │   │   │   ├── users.py
│   │   │   │   └── ...
│   │   │   └── __init__.py
│   │   └── __init__.py
│   │
│   ├── core/                 # Ядро приложения
│   │   ├── config.py         # Конфигурация
│   │   └── elasticsearch.py  # Инициализация ES
│   │
│   ├── models/               # Pydantic модели
│   │   ├── schemas.py
│   │   └── ...
│   │
│   ├── services/             # Бизнес-логика
│   │   ├── item_service.py
│   │   ├── user_service.py
│   │   └── ...
│   │
│   ├── repositories/         # Работа с Elasticsearch
│   │   ├── item_repository.py
│   │   ├── user_repository.py
│   │   └── ...
│   │
│   ├── utils/                # Вспомогательные утилиты
│   │   └── ...
│   │
│   └── __init__.py
│
├── tests/                    # Тесты
│   ├── unit/                 # Юнит-тесты
│   │   ├── services/
│   │   ├── repositories/
│   │   └── ...
│   │
│   ├── integration/          # Интеграционные тесты
│   │   └── ...
│   │
│   └── conftest.py           # Фикстуры pytest
│
├── .env                      # Переменные окружения
├── requirements.txt          # Зависимости
└── main.py                   # Точка входа
```

## Ключевые принципы

1. **Разделение слоев**:
   - API слой (эндпоинты)
   - Сервисный слой (бизнес-логика)
   - Репозиторий слой (работа с Elasticsearch)

2. **Инверсия зависимостей**:
   - Сервисы зависят от абстракций репозиториев
   - API зависит от сервисов

3. **Тестируемость**:
   - Каждый слой можно тестировать изолированно
   - Легко мокать зависимости

## Пример реализации

### 1. Репозиторий (Elasticsearch слой)

app/repositories/item_repository.py:
```python
from elasticsearch import AsyncElasticsearch
from app.core.config import settings

class ItemRepository:
    def __init__(self, es: AsyncElasticsearch):
        self.es = es
        self.index = settings.ES_ITEMS_INDEX

    async def search_items(self, query: str, size: int = 10):
        body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["name^3", "description"]
                }
            }
        }
        return await self.es.search(index=self.index, body=body, size=size)

    # Другие методы работы с Elasticsearch
```

### 2. Сервис (бизнес-логика)

app/services/item_service.py:
```python
from typing import Optional
from app.repositories.item_repository import ItemRepository
from app.models.schemas import ItemOut

class ItemService:
    def __init__(self, item_repo: ItemRepository):
        self.item_repo = item_repo

    async def search_items(self, query: str, size: int = 10) -> Optional[list[ItemOut]]:
        es_response = await self.item_repo.search_items(query, size)
        if not es_response:
            return None
            
        return [ItemOut(**hit["_source"]) for hit in es_response["hits"]["hits"]]
```

### 3. API слой (эндпоинты)

app/api/v1/endpoints/items.py:
```python
from fastapi import APIRouter, Depends
from app.services.item_service import ItemService
from app.models.schemas import ItemOut
from app.dependencies import get_item_service

router = APIRouter()

@router.get("/items/search", response_model=list[ItemOut])
async def search_items(
    query: str,
    size: int = 10,
    item_service: ItemService = Depends(get_item_service)
):
    return await item_service.search_items(query, size)
```

### 4. Зависимости

app/dependencies.py:
```python
from fastapi import Request
from app.repositories.item_repository import ItemRepository
from app.services.item_service import ItemService
from app.core.elasticsearch import es_client

async def get_item_repository(request: Request) -> ItemRepository:
    return ItemRepository(request.app.state.es)

async def get_item_service(item_repo: ItemRepository = Depends(get_item_repository)) -> ItemService:
    return ItemService(item_repo)
```

### 5. Инициализация Elasticsearch

app/core/elasticsearch.py:
```python
from elasticsearch import AsyncElasticsearch
from app.core.config import settings

es_client: AsyncElasticsearch | None = None

async def get_es() -> AsyncElasticsearch:
    return es_client

async def connect_es():
    global es_client
    es_client = AsyncElasticsearch(hosts=[settings.ES_URL])

async def close_es():
    global es_client
    if es_client:
        await es_client.close()
```

## Тестирование

Пример юнит-теста для сервиса:

tests/unit/services/test_item_service.py:
```python
import pytest
from unittest.mock import AsyncMock
from app.services.item_service import ItemService
from app.models.schemas import ItemOut

@pytest.mark.asyncio
async def test_search_items():
    # Создаем mock репозитория
    mock_repo = AsyncMock()
    mock_repo.search_items.return_value = {
        "hits": {
            "hits": [
                {"_source": {"name": "Test", "description": "Test item"}},
                {"_source": {"name": "Test 2", "description": "Another item"}}
            ]
        }
    }
    
    # Тестируем сервис
    service = ItemService(mock_repo)
    result = await service.search_items("test")
    
    # Проверяем результаты
    assert len(result) == 2
    assert isinstance(result[0], ItemOut)
    mock_repo.search_items.assert_called_once_with("test", 10)
```

## Преимущества такой структуры

1. **Четкое разделение ответственности**:
   - Каждый слой отвечает только за свою часть функциональности

2. **Легкость тестирования**:
   - Можно тестировать каждый слой изолированно
   - Легко мокать зависимости

3. **Гибкость**:
   - Можно легко заменить Elasticsearch на другую СУБД
   - Можно рефакторить бизнес-логику без изменения API

4. **Масштабируемость**:
   - Легко добавлять новые функции
   - Четкая структура помогает в командной разработке

Такой подход соответствует принципам Clean Architecture и делает ваше приложение более поддерживаемым и тестируемым.