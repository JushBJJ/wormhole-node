import asyncio
import ssl
import websockets


async def client():
    uri = "wss://localhost:6969"  # Change the URI if necessary
    ssl_context = ssl._create_unverified_context()
    async with websockets.connect(uri, ssl=ssl_context) as websocket:
        # Function to send a message to the server
        async def send_message(message):
            await websocket.send(message)
            print(f"YOU: {message}")

        # Function to receive a message from the server
        async def receive_message():
            response = await websocket.recv()
            print(f"SERVER: {response}")

        # Example of interaction
        await receive_message()  # Wait for connection acknowledgment

        # Send commands or messages
        await send_message("SEND message Hello, World!")
        await receive_message()  # Receive response

        await send_message("RCVE message 5")
        await receive_message()  # Receive messages

        await send_message("HELP")
        await receive_message()  # Receive help

        await send_message("X")
        await receive_message()  # Receive help

        # Close the connection
        await send_message("CLOSE")
        # The server might not send a response to CLOSE, adjust as needed


if __name__ == "__main__":
    asyncio.run(client())
