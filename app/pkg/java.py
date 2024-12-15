import asyncio
import json
from typing import List
import socket

class MapCommands:
    LIST_FLOWER = 1
    ADD_FLOWER = 3
    STOP = 7


class Client:
    def __init__(self):
        self.shop = None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.socket.connect(('java-server', 3345))
        except Exception as e:
            print(f"Error connecting to server: {e}")

    async def send_command(self, command: int):
        try:
            self.socket.sendall(command.to_bytes(1, 'big'))
        except IOError as e:
            print(f"Error sending command: {e}")

    async def get_object(self) -> str:
        try:
            raw_data = self.socket.recv(1024)
            print(f"Raw data received: {raw_data}")

            json_data = raw_data[2:]
            data = json_data.decode('utf-8')
            return data
        except UnicodeDecodeError as e:
            print(f"UnicodeDecodeError: {e}")
            return None
        except IOError as e:
            print(f"Error receiving object: {e}")
            return None

    async def send_object(self, obj):
        try:
            json_data = json.dumps(obj, default=lambda o: o.__dict__)
            print(json_data)
            self.socket.sendall(json_data.encode('utf-8'))
        except IOError as e:
            print(f"Error sending object: {e}")

    async def get_all_flowers(self) -> List[dict]:
        await self.send_command(MapCommands.LIST_FLOWER)
        flowers_json = await self.get_object()
        if flowers_json:
            flowers = json.loads(flowers_json)
            return flowers
        return []

    async def add_flower(self, flower: dict):
        await self.send_command(MapCommands.ADD_FLOWER)
        await self.send_object(flower)

    async def server_stopped(self):
        await self.send_command(MapCommands.STOP)
        try:
            self.socket.close()
        except IOError as e:
            print(f"Error closing socket: {e}")


if __name__ == '__main__':
    client = Client()

    flowerAdd = {"name": "MyTestFlower2", "color": "Blue", "price": 210.0, "quantity": 0, "id": 0}
    client.add_flower(flowerAdd)
    client.server_stopped()
