#!/bin/bash

# This script just provides a simpler way to use the ws_event_logger.

# Assumes $SCARAB_HOME is set to the root Scarab project where the virtual environment exists and the virtual
# environment is in .venv.
source "$SCARAB_HOME"/.venv/bin/activate
cd "$SCARAB_HOME" || exit

# Start using the default host and port.
python -m scarab.tools.ws_event_logger
