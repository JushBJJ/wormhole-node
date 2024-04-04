import asyncio
import ssl
import websockets
from collections import deque
from itertools import islice
from dotenv import load_dotenv


class Commands:
    def __init__(self):
        self.commands = dict({})

    def __iter__(self):
        return iter(self.commands)

    def register(self, type, name, func, doc):
        self.commands[type] = {"name": name, "func": func, "doc": doc}

    def get(self, command):
        return self.commands.get(command, None)


class Connection:
    def __init__(
        self,
        host="localhost",
        port=6969,
        certfile=None,
        keyfile=None,
        max_connections=12,
        max_messages=50,
    ):
        self.host = host
        self.port = port
        self.certfile = certfile
        self.keyfile = keyfile

        self.commands = Commands()
        self.messages = deque(maxlen=max_messages)
        self.max_connections = max_connections
        self.connections = set()

        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.ssl_context.load_cert_chain(certfile, keyfile)

    async def handle_connection(self, websocket, path):
        if len(self.connections) >= self.max_connections:
            await websocket.send(
                "Server is full: maximum number of connections reached."
            )
            return

        self.connections.add(websocket)
        try:
            await websocket.send(
                "You are connected. Type 'HELP' to see available commands."
            )
            async for message in websocket:
                command = message[:3]
                arg = message[4:]

                if command in list(self.commands):
                    response = self.commands.get(command)["func"](arg)
                    await websocket.send(response)
                else:
                    await websocket.send(
                        "Invalid command. Type 'HELP' to see available commands."
                    )
        finally:
            self.connections.remove(websocket)

    async def start_server(self):
        async with websockets.serve(
            self.handle_connection, self.host, self.port, ssl=self.ssl_context
        ):
            print(f"Server started at {self.host}:{self.port}")
            await asyncio.Future()

    def register_command(self, type, name, func, doc):
        self.commands.register(type, name, func, doc)

    # Send
    def send_message(self, arg):
        self.messages.append(arg)
        return True

    def upload_image(self, arg):
        pass

    # Receive
    def get_messages(self, arg):
        try:
            length = int(arg)
        except ValueError:
            return "Invalid argument. Please provide a number."
        return list(islice(self.messages, length))

    # Help
    def get_help(self):
        pass

    # Close
    def close(self):
        pass


async def main():
    conn = Connection(certfile="cert.pem", keyfile="key.pem")
    conn.register_command("SEND", "message", conn.send_message, "Send a message.")
    conn.register_command("SEND", "image", conn.upload_image, "Upload an image.")
    conn.register_command("RCVE", "message", conn.get_messages, "Get messages.")
    conn.register_command("HELP", "", conn.get_help, "Show help for commands.")
    conn.register_command("CLOSE", "", conn.close, "Close the server.")

    await conn.start_server()


if __name__ == "__main__":
    asyncio.run(main())
