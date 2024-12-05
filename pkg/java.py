import socket
import json


class Client:

    def __init__(self, host='localhost', port=3345):  # Corrected __init__ method
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))

    def send_command(self, command: int):
        try:
            self.socket.sendall(command.to_bytes(1, byteorder='big'))
        except Exception as e:
            print(f"Error send command: {e}")

    def get_object(self):
        try:
            data = self.socket.recv(1024)
            print("Data from socket", data)
            return data.decode('utf-8').split("[")[1].split("]")[0]
        except Exception as e:
            print(f"Error get_object: {e}")
            return None

    def send_text(self, text):
        try:
            # Ensure the text is a string
            if not isinstance(text, str):
                raise ValueError("The input must be a string.")

            # Encode as UTF-8 and create a bytes-like object
            encoded_text = text.encode('utf-8')

            # Prepare modified UTF-8 format with the length prefix
            length = len(encoded_text)
            self.socket.sendall(length.to_bytes(2, 'big') + encoded_text)

        except Exception as e:
            print(f"Error sending text: {e}")

    def send_object(self, obj):
        try:
            json_data = json.dumps(obj)
            print(json_data)
            self.socket.sendall(json_data.encode('utf-8'))
            # self.socket.sendall(obj.encode('utf-8'))
        except Exception as e:
            print(f"Error send object: {e}")

    def server_stopped(self):
        self.send_command(MapCommands.STOPPED)
        self.socket.close()

    def get_all_flowers(self):
        self.send_command(MapCommands.LIST_FLOWER)
        flowers_json = self.get_object()
        print("Flowers json", flowers_json)
        return json.loads(f"[{flowers_json}]") if flowers_json else []

    def add_flower(self, flower):
        self.send_command(MapCommands.ADD_FLOWER)
        self.send_object(json.dumps(flower))


class MapCommands:
    LIST_FLOWER = 1
    ADD_FLOWER = 3
    STOPPED = 6


if __name__ == "__main__":
    client = Client()
    try:
        flower = {"name": "Sunflower7", "color": "Yellow3", "price": 101.0, "quantity": 0, "id": 0}
        client.add_flower(flower)

    # flo = client.get_all_flowers()
    except Exception as e:
        print(f"Error get_all_flowers: {e}")
    finally:
        client.send_command(6)
