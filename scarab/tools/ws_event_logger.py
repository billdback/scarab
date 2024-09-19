"""
This event logger will connect to the simulation web socket server and listen for events and then log to the console.
"""

import asyncio
import json
import sys
from json import JSONDecodeError

import websockets

from scarab.framework.events import ScarabEventType


async def receive_events(server_url) -> None:
    """
    Creates a connection to the server and then logs messages to the console.
    :param server_url: The URL or IP of the server.
    """
    shutdown = False
    retries = 0
    max_retries = 10

    while retries < max_retries and not shutdown:
        try:
            print(f'connecting to server (try {retries} of {max_retries})')
            async with websockets.connect(server_url) as websocket:

                while not shutdown:
                    try:

                        # get and log events
                        response = await websocket.recv()
                        event = json.loads(response)
                        print(json.dumps(event))

                        # check for simulation shutdown.
                        if event.get('event_name', None) == ScarabEventType.SIMULATION_SHUTDOWN.value:
                            shutdown = True

                    # handle non-event messages
                    except JSONDecodeError:
                        print(f"Unexpected message (not JSON): {event}")

                    # check for server closed.
                    except websockets.ConnectionClosed:
                        print("Connection closed by server.")
                        shutdown = True

        except OSError as oserr:
            print(f"Error connecting to the server: {oserr}")
            retries += 1
            await asyncio.sleep(3)


if __name__ == "__main__":
    # get server_url and port as command line arguments
    server_url = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    server_port = str(sys.argv[2]) if len(sys.argv) > 2 else 12345
    ws_url = f"ws://{server_url}:{server_port}"

    # run until shutdown.
    try:
        asyncio.run(receive_events(ws_url))
    except OSError as e:
        print("Connection failed. Error: " + str(e))
        print("Check that the server is running and the client can connect.")
