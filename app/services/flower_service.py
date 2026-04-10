from typing import Any

from app.pkg.java import Client


class FlowerService:
    async def get_all_flowers(self) -> list[dict[str, Any]]:
        client = Client()
        flowers = await client.get_all_flowers()
        await client.server_stopped()
        return flowers

    async def add_flower(self, flower: dict[str, Any]) -> None:
        client = Client()
        await client.add_flower(flower)
        await client.server_stopped()
