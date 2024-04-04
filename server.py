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
        if self.commands.get(type) is None:
            self.commands[type] = dict({})

        # Append the command to the dictionary
        self.commands[type][name] = {"func": func, "doc": doc}

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

    async def invalid_command(self, websocket):
        try:
            await websocket.send(
                "Invalid command. Type 'HELP' to see available commands."
            )
        except websockets.exceptions.ConnectionClosedOK as e:
            print(e)

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
            print(f"Connection established: {websocket.remote_address}")
            async for message in websocket:
                if message.strip() == "":
                    await self.invalid_command(websocket)
                else:
                    print(f"{websocket.remote_address} > {message}")
                    command = message[:4].upper()

                    func_name, *rest = message.strip()[5:].split(maxsplit=1) + [None]
                    arg = rest[0] if rest else ""

                    if func_name and not func_name.strip():
                        func_name = ""

                    if command in list(self.commands):
                        # Check for no func_address commands
                        command = self.commands.get(command)

                        if command.get("DEFAULT", None):
                            func_address = command.get("DEFAULT").get("func")
                        else:
                            func_address = command.get(func_name).get("func")

                        if func_address is None:
                            await self.invalid_command(websocket)
                            continue

                        response = str(func_address(arg))
                        await websocket.send(response)
                    else:
                        await self.invalid_command(websocket)
        finally:
            self.connections.remove(websocket)

    async def start_server(self):
        async with websockets.serve(
            self.handle_connection, self.host, self.port, ssl=self.ssl_context
        ):
            print(f"Server started at {self.host}:{self.port}")
            await asyncio.Future()

    def register_command(self, type, name, func, doc, no_args=False):
        if no_args:
            self.commands.register(type, "DEFAULT", func, doc)
        else:
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
    def get_help(self, *args):
        help_message = ""
        help_message += f"COMMANDS: [{list(self.commands)}"
        return help_message

    # Close
    def close(self, *args):
        pass


async def main():
    conn = Connection(certfile="ssl/server.crt", keyfile="ssl/server.key")
    conn.register_command("SEND", "message", conn.send_message, "Send a message.")
    conn.register_command("SEND", "image", conn.upload_image, "Upload an image.")
    conn.register_command("RCVE", "message", conn.get_messages, "Get messages.")
    conn.register_command(
        "HELP", "", conn.get_help, "Show help for commands.", no_args=True
    )
    conn.register_command("CLOSE", "", conn.close, "Close the server.", no_args=True)

    await conn.start_server()


if __name__ == "__main__":
    asyncio.run(main())
