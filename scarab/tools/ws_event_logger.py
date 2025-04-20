"""
Copyright (c) 2024 William D Back

This file is part of Scarab licensed under the MIT License.
For full license text, see the LICENSE file in the project root.

This event logger will connect to the simulation web socket server and listen for events and then log to the console.
"""

import argparse
import asyncio
import json
from json import JSONDecodeError

import websockets

from scarab.framework.events import ScarabEventType


async def receive_events(server_url) -> None:
    """
    Creates a connection to the server and then logs messages to the console.
    :param server_url: The URL or IP of the server.
    """
    shutdown = False
    retry_count = 0
    max_retries = 10

    while retry_count < max_retries and not shutdown:
        try:
            print(f'connecting to server (try {retry_count} of {max_retries})')
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

        except OSError:
            retry_count += 1
            if retry_count < max_retries:
                print("Retrying in 3 seconds...")
                await asyncio.sleep(3)
            else:
                print("Max retries reached. Exiting.")
                return


def main():
    """
    Main entry point for the event logger.
    Parses command line arguments and connects to the WebSocket server to log events.
    """
    # get server_url and port as command line arguments
    parser = argparse.ArgumentParser(description='Connect to a WebSocket and log events.')
    parser.add_argument('--host', default='localhost', help='WebSocket host (default: localhost)')
    parser.add_argument('--port', type=int, default=1234, help='WebSocket port (default: 1234)')
    args = parser.parse_args()

    ws_url = f"ws://{args.host}:{args.port}"

    # run until shutdown or interrupt.
    try:
        asyncio.run(receive_events(ws_url))
    except KeyboardInterrupt:
        print('^C received, shutting down the logger.')


if __name__ == "__main__":
    main()
