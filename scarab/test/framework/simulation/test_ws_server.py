"""
Copyright (c) 2024 William D Back

This file is part of Scarab licensed under the MIT License.
For full license text, see the LICENSE file in the project root.

Tests for the WebSocket server implementation in _ws_server.py.
"""
import asyncio
import json
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import dataclasses

from scarab.framework.events import Event, EntityCreatedEvent
from scarab.framework.simulation._ws_server import WSEventServer
from scarab.framework.entity import scarab_properties

# Mock the websockets module
class MockConnectionClosed(Exception):
    def __init__(self, code, reason):
        self.code = code
        self.reason = reason
        super().__init__(f"Connection closed: {code} {reason}")

# Create a mock websockets module
class MockWebsockets:
    ConnectionClosed = MockConnectionClosed

# Use the mock instead of the real module
websockets = MockWebsockets()


class TestWSEventServer:
    """Tests for the WSEventServer class."""

    @pytest.fixture
    def mock_simulation(self):
        """Creates a mock simulation for testing."""
        sim = MagicMock()
        sim._entities = {}
        sim._current_time = 0
        return sim

    @pytest.fixture
    def ws_server(self, mock_simulation):
        """Creates a WSEventServer instance for testing."""
        return WSEventServer(sim=mock_simulation, host='localhost', port=8765)

    def test_init(self, ws_server, mock_simulation):
        """Tests initialization of the WSEventServer."""
        assert ws_server._sim_owner == mock_simulation
        assert ws_server._host == 'localhost'
        assert ws_server._port == 8765
        assert ws_server._clients == set()
        assert ws_server._server is None
        assert ws_server._is_running is False
        assert isinstance(ws_server._stop_event, asyncio.Event)

    def test_is_running_property(self, ws_server):
        """Tests the is_running property."""
        assert ws_server.is_running is False
        ws_server._is_running = True
        assert ws_server.is_running is True

    @pytest.mark.asyncio
    async def test_start_server_not_running(self, ws_server):
        """Tests starting the server when it's not already running."""
        # Mock the _run_server method to avoid actually starting a server
        with patch.object(ws_server, '_run_server', new_callable=AsyncMock) as mock_run:
            with patch('asyncio.create_task') as mock_create_task:
                await ws_server.start_server()

                # Verify the stop event was cleared
                assert not ws_server._stop_event.is_set()

                # Verify create_task was called with _run_server
                mock_create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_server_already_running(self, ws_server):
        """Tests starting the server when it's already running."""
        ws_server._is_running = True

        # Mock the _run_server method to avoid actually starting a server
        with patch.object(ws_server, '_run_server', new_callable=AsyncMock) as mock_run:
            with patch('asyncio.create_task') as mock_create_task:
                await ws_server.start_server()

                # Verify create_task was not called
                mock_create_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_stop_server_with_clients(self, ws_server):
        """Tests stopping the server when clients are connected."""
        # Setup mock clients
        client1 = AsyncMock()
        client2 = AsyncMock()
        ws_server._clients = {client1, client2}
        ws_server._is_running = True
        ws_server._server = MagicMock()
        ws_server._server.wait_closed = AsyncMock()

        await ws_server.stop_server()

        # Verify clients were closed
        client1.close.assert_called_once()
        client2.close.assert_called_once()

        # Verify server was stopped
        assert ws_server._stop_event.is_set()
        ws_server._server.wait_closed.assert_called_once()
        assert not ws_server._is_running

    @pytest.mark.asyncio
    async def test_stop_server_no_clients(self, ws_server):
        """Tests stopping the server when no clients are connected."""
        ws_server._clients = set()
        ws_server._is_running = True
        ws_server._server = MagicMock()
        ws_server._server.wait_closed = AsyncMock()

        await ws_server.stop_server()

        # Verify server was stopped
        assert ws_server._stop_event.is_set()
        ws_server._server.wait_closed.assert_called_once()
        assert not ws_server._is_running

    @pytest.mark.asyncio
    async def test_send_event_with_clients(self, ws_server):
        """Tests sending an event when clients are connected."""
        # Setup mock clients
        client1 = AsyncMock()
        client2 = AsyncMock()
        ws_server._clients = {client1, client2}

        # Create a test event
        event = Event(event_name="test_event")

        await ws_server.send_event(event)

        # Verify send was called on each client with the correct message
        expected_message = json.dumps(event.to_json())
        client1.send.assert_called_once_with(expected_message)
        client2.send.assert_called_once_with(expected_message)

    @pytest.mark.asyncio
    async def test_send_event_no_clients(self, ws_server):
        """Tests sending an event when no clients are connected."""
        ws_server._clients = set()

        # Create a test event
        event = Event(event_name="test_event")

        # This should not raise any exceptions
        await ws_server.send_event(event)

    @pytest.mark.asyncio
    async def test_send_event_type_error(self, ws_server):
        """Tests sending an event that causes a TypeError."""
        # Setup mock client
        client = AsyncMock()
        ws_server._clients = {client}

        # Create a mock event that will cause a TypeError when to_json is called
        event = MagicMock()
        event.event_name = "test_event"
        event.to_json.side_effect = TypeError("Test error")

        # This should not raise any exceptions
        await ws_server.send_event(event)

        # Verify client.send was not called
        client.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_client_message_start(self, ws_server):
        """Tests handling a 'start' message from a client."""
        await ws_server._handle_client_message("start")
        ws_server._sim_owner.resume.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_client_message_resume(self, ws_server):
        """Tests handling a 'resume' message from a client."""
        await ws_server._handle_client_message("resume")
        ws_server._sim_owner.resume.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_client_message_pause(self, ws_server):
        """Tests handling a 'pause' message from a client."""
        await ws_server._handle_client_message("pause")
        ws_server._sim_owner.pause.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_client_message_shutdown(self, ws_server):
        """Tests handling a 'shutdown' message from a client."""
        await ws_server._handle_client_message("shutdown")
        ws_server._sim_owner.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_client_message_unknown(self, ws_server):
        """Tests handling an unknown message from a client."""
        with patch('builtins.print') as mock_print:
            await ws_server._handle_client_message("unknown")
            mock_print.assert_called_once_with("Unknown command unknown")

    @pytest.mark.asyncio
    async def test_send_all_entities(self, ws_server, mock_simulation):
        """Tests sending all entities to a new client."""
        # Create a mock entity with proper scarab properties
        entity = MagicMock()
        entity.__class__.__name__ = "TestEntity"
        entity.scarab_name = "test_entity"
        entity.scarab_id = "test_id"
        entity.scarab_conforms_to = None  # Set to None to use the non-conforming path in scarab_properties

        # Add the entity to the simulation
        mock_simulation._entities = {"entity1": entity}

        # Create a mock websocket
        websocket = AsyncMock()

        # Mock scarab_properties to avoid dataclass issues
        with patch('scarab.framework.entity.scarab_properties', return_value={
            'scarab_name': 'test_entity',
            'scarab_id': 'test_id'
        }):
            # Call _send_all_entities
            await ws_server._send_all_entities(websocket)

        # Verify websocket.send was called
        websocket.send.assert_called_once()

        # Verify the message contains the entity data
        call_args = websocket.send.call_args[0][0]
        assert "scarab.entity.created" in call_args

    @pytest.mark.asyncio
    async def test_send_all_entities_exception(self, ws_server, mock_simulation):
        """Tests handling an exception when sending entities to a new client."""
        # Create a mock entity with proper scarab properties
        entity = MagicMock()
        entity.__class__.__name__ = "TestEntity"
        entity.scarab_name = "test_entity"
        entity.scarab_id = "test_id"
        entity.scarab_conforms_to = None  # Set to None to use the non-conforming path in scarab_properties

        # Add the entity to the simulation
        mock_simulation._entities = {"entity1": entity}

        # Create a mock websocket that raises an exception
        websocket = AsyncMock()
        websocket.send.side_effect = Exception("Test exception")
        websocket.remote_address = "test_address"

        # Mock scarab_properties to avoid dataclass issues
        with patch('scarab.framework.entity.scarab_properties', return_value={
            'scarab_name': 'test_entity',
            'scarab_id': 'test_id'
        }):
            # Call _send_all_entities - should not raise an exception
            await ws_server._send_all_entities(websocket)

    @pytest.mark.asyncio
    async def test_handle_client(self, ws_server):
        """Tests the _handle_client method."""
        # Create a mock websocket
        websocket = AsyncMock()
        websocket.remote_address = "test_address"

        # Mock the _send_all_entities method
        with patch.object(ws_server, '_send_all_entities', new_callable=AsyncMock) as mock_send:
            # Mock the websocket.__aiter__ to return messages
            websocket.__aiter__.return_value = ["message1", "message2"]

            # Mock the _handle_client_message method
            with patch.object(ws_server, '_handle_client_message', new_callable=AsyncMock) as mock_handle:
                # Call _handle_client
                await ws_server._handle_client(websocket)

                # Verify the client was added and removed
                assert websocket not in ws_server._clients

                # Verify _send_all_entities was called
                mock_send.assert_called_once_with(websocket)

                # Verify _handle_client_message was called for each message
                assert mock_handle.call_count == 2
                mock_handle.assert_any_call("message1")
                mock_handle.assert_any_call("message2")

    @pytest.mark.asyncio
    async def test_handle_client_connection_closed(self, ws_server):
        """Tests that the _handle_client method properly handles ConnectionClosed exceptions."""
        # Create a mock websocket
        websocket = AsyncMock()
        websocket.remote_address = "test_address"

        # Mock the _send_all_entities method to avoid that part of the code
        with patch.object(ws_server, '_send_all_entities', new_callable=AsyncMock) as mock_send:
            # Let's try a simpler approach - directly patch the websocket's methods
            # Make __aiter__ return the websocket itself
            websocket.__aiter__ = AsyncMock(return_value=websocket)

            # Make __anext__ raise ConnectionClosed when called
            websocket.__anext__ = AsyncMock(side_effect=websockets.ConnectionClosed(1000, "Test close"))

            # Mock the logger to verify it's called
            with patch('scarab.framework.simulation._ws_server.logger.debug') as mock_logger:
                # Call _handle_client
                await ws_server._handle_client(websocket)

                # Verify logger.debug was called with the client disconnected message
                mock_logger.assert_any_call(f"Client disconnected: {websocket.remote_address}")

                # Verify the client was added and then removed
                assert websocket not in ws_server._clients

    @pytest.mark.asyncio
    async def test_run_server(self, ws_server):
        """Tests the _run_server method."""
        # Mock the websockets.serve function
        mock_server = MagicMock()

        with patch('websockets.serve', return_value=mock_server) as mock_serve:
            # Start the task but don't await it
            task = asyncio.create_task(ws_server._run_server())

            # Give the task a moment to start
            await asyncio.sleep(0.1)

            # Verify the server is running
            assert ws_server._is_running is True

            # Signal the server to stop
            ws_server._stop_event.set()

            # Wait for the task to complete
            await task

            # Verify serve was called with the correct arguments
            mock_serve.assert_called_once_with(ws_server._handle_client, ws_server._host, ws_server._port)
