from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI

from app.core.config import get_es_url
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = httpx.AsyncClient(base_url=get_es_url(), timeout=settings.ES_TIMEOUT)
    app.state.es_client = client
    try:
        yield
    finally:
        await client.aclose()


def get_es_client(app: FastAPI) -> httpx.AsyncClient:
    return app.state.es_client


async def ensure_index(client: httpx.AsyncClient) -> bool:
    index_name = settings.ES_INDEX
    try:
        response = await client.head(f"/{index_name}")
        if response.status_code == 200:
            return True
        if response.status_code not in {404, 405}:
            return False

        payload: dict[str, Any] = {
            "settings": {
                "analysis": {
                    "filter": {
                        "russian_stop": {
                            "type": "stop",
                            "stopwords": "_russian_",
                        },
                        "group_names_stop": {
                            "type": "stop",
                            "stopwords": ["дима", "артем", "сергей"],
                        },
                        "russian_stemmer": {
                            "type": "stemmer",
                            "language": "russian",
                        },
                        "secrecy_synonyms": {
                            "type": "synonym",
                            "synonyms": [
                                "секретно => неинтересно",
                                "совершенно секретно => неинтересно",
                                "конфиденциально => неинтересно",
                                "для служебного пользования => неинтересно",
                            ],
                        },
                    },
                    "analyzer": {
                        "todo_russian": {
                            "tokenizer": "standard",
                            "filter": [
                                "lowercase",
                                "secrecy_synonyms",
                                "russian_stop",
                                "group_names_stop",
                                "russian_stemmer",
                            ],
                        }
                    },
                }
            },
            "mappings": {
                "properties": {
                    "id": {"type": "integer"},
                    "title": {"type": "text", "analyzer": "todo_russian"},
                    "details": {"type": "text", "analyzer": "todo_russian"},
                    "tag": {
                        "type": "text",
                        "analyzer": "todo_russian",
                        "fields": {"keyword": {"type": "keyword"}},
                    },
                    "source": {
                        "type": "text",
                        "analyzer": "todo_russian",
                        "fields": {"keyword": {"type": "keyword"}},
                    },
                    "created_at": {"type": "date"},
                    "attachment_name": {"type": "keyword"},
                    "attachment_text": {"type": "text", "analyzer": "todo_russian"},
                }
            },
        }
        create_response = await client.put(f"/{index_name}", json=payload)
        return create_response.status_code in {200, 201}
    except httpx.HTTPError:
        return False
