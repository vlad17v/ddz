import socket
import json
from typing import List


class MapCommands:
    LIST_FLOWER = 1
    ADD_FLOWER = 3
    STOP = 7


class Client:
    def __init__(self):
        self.shop = None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect(('localhost', 3345))
        except Exception as e:
            print(f"Error connecting to server: {e}")

    def send_command(self, command: int):
        try:
            self.socket.sendall(command.to_bytes(1, 'big'))
        except IOError as e:
            print(f"Error sending command: {e}")

    def get_object(self) -> str:
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

    def send_object(self, obj):
        try:
            json_data = json.dumps(obj, default=lambda o: o.__dict__)
            print(json_data)
            self.socket.sendall(json_data.encode('utf-8'))
        except IOError as e:
            print(f"Error sending object: {e}")

    def get_all_flowers(self) -> List[dict]:
        self.send_command(MapCommands.LIST_FLOWER)
        flowers_json = self.get_object()
        if flowers_json:
            flowers = json.loads(flowers_json)
            return flowers
        return []

    def add_flower(self, flower: dict):
        self.send_command(MapCommands.ADD_FLOWER)
        self.send_object(flower)

    def server_stopped(self):
        self.send_command(MapCommands.STOP)
        try:
            self.socket.close()
        except IOError as e:
            print(f"Error closing socket: {e}")


if __name__ == '__main__':
    client = Client()
    flowers1 = client.get_all_flowers()
    print(flowers1)
    flowerAdd = {"name": "MyTestFlower2", "color": "Blue", "price": 210.0, "quantity": 0, "id": 0}
    client.add_flower(flowerAdd)
    client.server_stopped()
