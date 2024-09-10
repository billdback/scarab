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


if __name__ == "__main__":
    # get server_url and port as command line arguments
    server_url = "ws://" + sys.argv[1] + ":" + str(sys.argv[2])

    # run until shutdown.
    try:
        asyncio.run(receive_events(server_url))
    except OSError as e:
        print("Connection failed. Error: " + str(e))
        print("Check that the server is running and the client can connect.")

