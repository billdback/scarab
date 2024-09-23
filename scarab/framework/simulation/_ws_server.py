"""
Copyright (c) 2024 William D Back

This file is part of Scarab licensed under the MIT License.
For full license text, see the LICENSE file in the project root.

Web socket server the simulation uses to send events to web socket connections.
"""
import asyncio
import json
import logging
import websockets

from scarab.framework.entity import scarab_properties
from scarab.framework.events import Event, EntityCreatedEvent

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logger.setLevel(logging.WARNING)


class WSEventServer:

    # noinspection PyUnresolvedReferences
    def __init__(self, sim: 'Simulation', host='localhost', port=12345):
        """
        Creates a new web socket event server for sending and receiving events.
        :param sim: The simulation that owns the server.  It's used to allow events to call the simulation.
        :param host: The host address of the web socket server.
        :param port: The port of the web socket server.
        """
        self._sim_owner = sim
        self._host = host
        self._port = port

        self._clients = set()
        self._server = None
        self._is_running = False
        self._stop_event = asyncio.Event()

    @property
    def is_running(self):
        """Returns true if the server is running"""
        return self._is_running

    # noinspection PyUnusedLocal
    async def _handle_client(self, websocket, path):
        # Register client connection
        self._clients.add(websocket)
        logger.debug(f"Client connected: {websocket.remote_address}")

        await self._send_all_entities(websocket)

        try:
            async for message in websocket:
                await self._handle_client_message(message)
        except websockets.ConnectionClosed:
            logger.debug(f"Client disconnected: {websocket.remote_address}")
        finally:
            # Unregister client
            self._clients.remove(websocket)

    async def _send_all_entities(self, websocket: websockets) -> None:
        """
        When new clients connect, we want to send all the current entities.
        :param websocket: The websocket that just connected.
        """

        # noinspection PyProtectedMember
        for e in self._sim_owner._entities.values():
            # Sending as create entity messages since this is new to the client.  Note that reconnect must be handled
            # by the client.
            logger.debug(f"Sending entity to new connection: {e.__class__.__name__}")
            # noinspection PyProtectedMember
            evt = EntityCreatedEvent(entity_props=scarab_properties(e), sim_time=self._sim_owner._current_time)
            try:
                await websocket.send(json.dumps(evt.to_json()))
            except Exception as ex:
                logger.error(f"Error sending {evt} to {websocket.remote_address}: {ex}")

    async def start_server(self):
        """Starts the server and then returns."""
        if not self._is_running:
            self._stop_event.clear()  # Reset the stop event
            # noinspection PyUnusedLocal
            task = asyncio.create_task(self._run_server())
            logger.debug("Server task created and started")
        else:
            logger.debug("Server is already running")

    async def _run_server(self):
        """Runs the server"""
        logger.debug(f"Starting server on {self._host}:{self._port}")
        self._is_running = True
        # noinspection PyTypeChecker
        async with websockets.serve(self._handle_client, self._host, self._port) as server:
            self._server = server
            logger.debug(f"Server started on {self._host}:{self._port}")
            await self._stop_event.wait()

        logger.debug(f"Server started on {self._host}")

    async def stop_server(self):
        logger.debug(f"Server stopping...")
        self._is_running = False

        # Close all client connections
        if self._clients:
            await asyncio.gather(*(client.close() for client in self._clients))
        logger.debug("All clients disconnected.")

        # Close server
        self._stop_event.set()  # Signal the server to stop
        if self._server:
            await self._server.wait_closed()  # Wait until the server is fully closed
        self._is_running = False

        logger.debug("Server shut down.")

    async def send_event(self, event: Event):
        logger.debug(f'  WSEventServer: Sending event: {event.event_name}')
        print(f'  WSEventServer: Sending event: {event.event_name}')
        if self._clients:
            try:
                message = json.dumps(event.to_json())
                await asyncio.gather(*(client.send(message) for client in self._clients))
                logger.debug(f"Sent message to all clients: {message}")
            except TypeError as err:
                logger.error(f'Unable to send {event}: {err}')
        else:
            logger.debug("No clients connected.")

    async def _handle_client_message(self, message) -> None:
        """
        Handles messages from the websocket clients.
        :param message: The message that the client sent.
        """
        logger.debug(f'Message from client: {message}')

        # sim should be already running, so start is just resume.
        if message == 'start' or message == 'resume':
            self._sim_owner.resume()
        elif message == 'pause':
            self._sim_owner.pause()
        elif message == 'shutdown':
            self._sim_owner.shutdown()
        else:
            print(f'Unknown command {message}')
