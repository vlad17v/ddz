from datetime import datetime
from typing import Any

import httpx
from loguru import logger

from app.core.config import settings
from app.core.elasticsearch import ensure_index


class TodoSearchRepository:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        self.index = settings.ES_INDEX
        self._index_ready = False

    async def _prepare_index(self) -> bool:
        if self._index_ready:
            return True
        self._index_ready = await ensure_index(self.client)
        return self._index_ready

    async def index_todo(self, todo_id: int, document: dict[str, Any]) -> bool:
        if not await self._prepare_index():
            return False
        try:
            response = await self.client.put(f"/{self.index}/_doc/{todo_id}", json=document)
            return response.status_code in {200, 201}
        except httpx.HTTPError as err:
            logger.warning(f"Elasticsearch index failed for todo {todo_id}: {err}")
            return False

    async def delete_todo(self, todo_id: int) -> bool:
        if not await self._prepare_index():
            return False
        try:
            response = await self.client.delete(f"/{self.index}/_doc/{todo_id}")
            return response.status_code in {200, 404}
        except httpx.HTTPError as err:
            logger.warning(f"Elasticsearch delete failed for todo {todo_id}: {err}")
            return False

    async def search_todos(
        self,
        *,
        query: str | None,
        tag: str | None,
        creation_date_start: datetime | None,
        creation_date_end: datetime | None,
        skip: int,
        limit: int,
    ) -> dict[str, Any] | None:
        if not await self._prepare_index():
            return None

        filters: list[dict[str, Any]] = []
        must: list[dict[str, Any]] = []

        if tag:
            filters.append({"term": {"tag.keyword": tag}})

        if creation_date_start or creation_date_end:
            range_query: dict[str, Any] = {}
            if creation_date_start:
                range_query["gte"] = creation_date_start.isoformat()
            if creation_date_end:
                range_query["lte"] = creation_date_end.isoformat()
            filters.append({"range": {"created_at": range_query}})

        if query:
            must.append(
                {
                    "multi_match": {
                        "query": query,
                        "fields": ["title^3", "details^2", "tag", "attachment_text"],
                    }
                }
            )

        body: dict[str, Any] = {
            "from": skip * limit,
            "size": limit,
            "sort": [{"created_at": {"order": "desc"}}, {"id": {"order": "desc"}}],
            "query": {
                "bool": {
                    "must": must or [{"match_all": {}}],
                    "filter": filters,
                }
            },
        }
        try:
            response = await self.client.post(f"/{self.index}/_search", json=body)
            if response.status_code != 200:
                return None
            payload = response.json()
            hits = payload.get("hits", {})
            return {
                "ids": [hit["_source"]["id"] for hit in hits.get("hits", [])],
                "total": hits.get("total", {}).get("value", 0),
            }
        except httpx.HTTPError as err:
            logger.warning(f"Elasticsearch search failed: {err}")
            return None

    async def analyze_texts(self, texts: list[str]) -> list[str] | None:
        filtered_texts = [text for text in texts if text]
        if not filtered_texts:
            return []
        if not await self._prepare_index():
            return None

        body = {
            "analyzer": "todo_russian",
            "text": filtered_texts,
        }
        try:
            response = await self.client.post(f"/{self.index}/_analyze", json=body)
            if response.status_code != 200:
                return None
            payload = response.json()
            return [token["token"] for token in payload.get("tokens", []) if token.get("token")]
        except httpx.HTTPError as err:
            logger.warning(f"Elasticsearch analyze failed: {err}")
            return None
