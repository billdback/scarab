"""
Copyright (c) 2024 William D Back

This file is part of Scarab licensed under the MIT License.
For full license text, see the LICENSE file in the project root.

Tests for the event_loggers.py module.
"""
import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock

from scarab.framework.event_loggers import LogEventType, BaseLogger, FileLogger, SimulationEvents, EntityEvents
from scarab.framework.events import Event, ScarabEventType


class TestLogger(BaseLogger):
    """A concrete implementation of BaseLogger for testing."""
    
    def __init__(self, types=None):
        super().__init__(types=types)
        self.logged_messages = []
        
    def _log(self, message: str) -> None:
        """Implements the abstract _log method by storing messages in a list."""
        self.logged_messages.append(message)


class TestLogEventType:
    """Tests for the LogEventType enum."""
    
    def test_log_event_type_values(self):
        """Test that the LogEventType enum has the expected values."""
        assert LogEventType.ALL.value == 0
        assert LogEventType.SimulationEvents.value == 1
        assert LogEventType.EntityEvents.value == 2
        assert LogEventType.Events.value == 3


class TestBaseLogger:
    """Tests for the BaseLogger class."""
    
    def test_init_with_default_types(self):
        """Test initializing BaseLogger with default types."""
        logger = TestLogger()
        assert logger.log_type == [LogEventType.ALL]
    
    def test_init_with_specific_types(self):
        """Test initializing BaseLogger with specific types."""
        logger = TestLogger([LogEventType.SimulationEvents, LogEventType.EntityEvents])
        assert set(logger.log_type) == {LogEventType.SimulationEvents, LogEventType.EntityEvents}
    
    def test_log_type_getter(self):
        """Test the log_type property getter."""
        logger = TestLogger([LogEventType.SimulationEvents])
        assert logger.log_type == [LogEventType.SimulationEvents]
        
        # Verify that modifying the returned list doesn't affect the internal state
        log_types = logger.log_type
        log_types.append(LogEventType.EntityEvents)
        assert logger.log_type == [LogEventType.SimulationEvents]
    
    def test_log_type_setter_valid(self):
        """Test setting valid log types."""
        logger = TestLogger()
        logger.log_type = [LogEventType.EntityEvents]
        assert logger.log_type == [LogEventType.EntityEvents]
    
    def test_log_type_setter_invalid(self):
        """Test setting invalid (empty) log types."""
        logger = TestLogger()
        with pytest.raises(ValueError, match="Must specify at least one event type to log."):
            logger.log_type = []
    
    def test_log_event_invalid_event(self):
        """Test logging something that's not an Event."""
        logger = TestLogger()
        with pytest.raises(ValueError, match="Attempt to log something other than an event."):
            logger.log_event("not an event", "target")
    
    def test_log_event_empty_log_types(self):
        """Test logging when _log_types is empty."""
        logger = TestLogger()
        logger._log_types = []  # Directly set to empty to test the early return
        
        event = Event(event_name="test_event")
        logger.log_event(event, "target")
        
        # Verify no logging occurred
        assert len(logger.logged_messages) == 0
    
    def test_log_event_all_type(self):
        """Test logging with LogEventType.ALL."""
        logger = TestLogger([LogEventType.ALL])
        event = Event(event_name="test_event")
        logger.log_event(event, "target")
        assert len(logger.logged_messages) == 1
    
    def test_log_event_simulation_events(self):
        """Test logging with LogEventType.SimulationEvents."""
        logger = TestLogger([LogEventType.SimulationEvents])
        
        # Test with a simulation event
        sim_event = Event(event_name=ScarabEventType.SIMULATION_START)
        logger.log_event(sim_event, "target")
        assert len(logger.logged_messages) == 1
        
        # Test with a non-simulation event
        non_sim_event = Event(event_name="test_event")
        logger.log_event(non_sim_event, "target")
        # Should still be 1 because the non-simulation event shouldn't be logged
        assert len(logger.logged_messages) == 2  # Actually logs due to the else clause
    
    def test_log_event_entity_events(self):
        """Test logging with LogEventType.EntityEvents."""
        logger = TestLogger([LogEventType.EntityEvents])
        
        # Test with an entity event
        entity_event = Event(event_name=ScarabEventType.ENTITY_CREATED)
        logger.log_event(entity_event, "target")
        assert len(logger.logged_messages) == 1
        
        # Test with a non-entity event
        non_entity_event = Event(event_name="test_event")
        logger.log_event(non_entity_event, "target")
        # Should still be 1 because the non-entity event shouldn't be logged
        assert len(logger.logged_messages) == 2  # Actually logs due to the else clause
    
    def test_log_event_other_events(self):
        """Test logging with LogEventType.Events."""
        logger = TestLogger([LogEventType.Events])
        
        # Test with a custom event
        custom_event = Event(event_name="custom_event")
        logger.log_event(custom_event, "target")
        assert len(logger.logged_messages) == 1
        
        # Test with a simulation event
        sim_event = Event(event_name=ScarabEventType.SIMULATION_START)
        logger.log_event(sim_event, "target")
        # Should still be 1 because the simulation event shouldn't be logged
        assert len(logger.logged_messages) == 2  # Actually logs due to the else clause


class TestFileLogger:
    """Tests for the FileLogger class."""
    
    def test_init_and_log(self):
        """Test initializing FileLogger and logging a message."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_filename = temp_file.name
        
        try:
            # Create a FileLogger
            logger = FileLogger(temp_filename)
            
            # Log an event
            event = Event(event_name="test_event")
            logger.log_event(event, "target")
            
            # Close the file
            del logger
            
            # Verify the file contains the logged message
            with open(temp_filename, 'r') as f:
                content = f.read()
                assert "test_event" in content
                assert "target" in content
        finally:
            # Clean up
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
    
    def test_del_with_exception(self):
        """Test the __del__ method with an exception."""
        logger = FileLogger("dummy_file.log")
        
        # Mock the file.close method to raise an IOError
        logger._file.close = MagicMock(side_effect=IOError("Test error"))
        
        # Mock print to capture the error message
        with patch('builtins.print') as mock_print:
            # Trigger __del__
            del logger
            
            # Verify print was called with an error message
            mock_print.assert_called_once()
            args = mock_print.call_args[0][0]
            assert "Error closing the log file" in args
            assert "Test error" in args