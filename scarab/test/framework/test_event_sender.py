"""
Copyright (c) 2024 William D Back

This file is part of Scarab licensed under the MIT License.
For full license text, see the LICENSE file in the project root.

Tests for the sender_id and target_id functionality in events.
"""

import pytest
from unittest.mock import MagicMock

from scarab.framework.entity import Entity
from scarab.framework.events import Event, ScarabEventType
from scarab.framework.simulation.simulation import Simulation


class MockSimulation:
    """A mock simulation that captures events sent by entities."""
    
    def __init__(self):
        self.events = []
    
    def send_event(self, event):
        """Captures events sent by entities."""
        self.events.append(event)


@Entity(name="SenderEntity")
class SenderEntity:
    """Entity that sends events and commands."""
    
    def __init__(self):
        self.received_events = []
        self.received_commands = []
    
    def send_test_event(self):
        """Sends a test event."""
        event = Event(event_name="test-event")
        self.send_event(event)
        return event
    
    def send_test_command(self, target_id):
        """Sends a test command to a specific entity."""
        event = Event(event_name="test-command")
        self.send_command(event, target_id)
        return event


@Entity(name="ReceiverEntity")
class ReceiverEntity:
    """Entity that receives events and commands."""
    
    def __init__(self):
        self.received_events = []
        self.received_commands = []
        self.last_sender_id = None
    
    def receive_event(self, event):
        """Receives an event."""
        self.received_events.append(event)
        self.last_sender_id = event.sender_id


def test_entity_send_event():
    """Tests that entities set sender_id when sending events."""
    # Create a mock simulation
    mock_sim = MockSimulation()
    
    # Create a sender entity
    sender = SenderEntity()
    sender.scarab_id = "sender-123"
    sender.scarab_simulation = mock_sim
    
    # Send an event
    event = sender.send_test_event()
    
    # Verify the event has the correct sender_id
    assert len(mock_sim.events) == 1
    assert mock_sim.events[0].sender_id == "sender-123"
    assert event.sender_id == "sender-123"


def test_entity_send_command():
    """Tests that entities set sender_id and target_id when sending commands."""
    # Create a mock simulation
    mock_sim = MockSimulation()
    
    # Create a sender entity
    sender = SenderEntity()
    sender.scarab_id = "sender-123"
    sender.scarab_simulation = mock_sim
    
    # Send a command
    target_id = "receiver-456"
    event = sender.send_test_command(target_id)
    
    # Verify the event has the correct sender_id and target_id
    assert len(mock_sim.events) == 1
    assert mock_sim.events[0].sender_id == "sender-123"
    assert mock_sim.events[0].target_id == "receiver-456"
    assert event.sender_id == "sender-123"
    assert event.target_id == "receiver-456"


def test_simulation_send_event():
    """Tests that the simulation sets sender_id=0 for events it sends."""
    # Create a simulation
    sim = Simulation()
    
    # Create an event
    event = Event(event_name="test-event")
    
    # Send the event through the simulation
    sim.send_event(event)
    
    # Verify the event has sender_id=0
    assert event.sender_id == "0"


def test_entity_conversation():
    """Tests that entities can have a conversation using sender_id and target_id."""
    # Create a mock simulation
    mock_sim = MockSimulation()
    
    # Create sender and receiver entities
    sender = SenderEntity()
    sender.scarab_id = "sender-123"
    sender.scarab_simulation = mock_sim
    
    receiver = ReceiverEntity()
    receiver.scarab_id = "receiver-456"
    
    # Send a command from sender to receiver
    event = Event(event_name="hello")
    sender.send_command(event, receiver.scarab_id)
    
    # Simulate the receiver getting the event
    receiver.receive_event(mock_sim.events[0])
    
    # Verify the receiver got the event with the correct sender_id
    assert len(receiver.received_events) == 1
    assert receiver.last_sender_id == "sender-123"
    
    # Now have the receiver respond to the sender
    response = Event(event_name="reply")
    receiver.scarab_simulation = mock_sim
    receiver.send_command(response, sender.scarab_id)
    
    # Verify the response has the correct sender_id and target_id
    assert len(mock_sim.events) == 2
    assert mock_sim.events[1].sender_id == "receiver-456"
    assert mock_sim.events[1].target_id == "sender-123"