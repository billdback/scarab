import argparse
import asyncio
import websockets
import aioconsole

from scarab.framework.events import SimulationStartEvent, SimulationPauseEvent, SimulationResumeEvent, \
    SimulationShutdownEvent

valid_commands = {
    'start': 'starts simulation execution',
    'pause': 'pauses simulation execution',
    'resume': 'resumes simulation execution',
    'shutdown': 'shuts down the simulation'
}


async def show_help(cmd: str = None):
    """
    Shows a help message, including an error if the command is invalid.
    :param cmd: The command that was entered.  If no command, then show help.
    """

    if cmd is not None:
        print(f"Invalid command: {cmd}")

    print("\nAvailable commands:\n")
    for command, description in valid_commands.items():
        print(f"\u2022 {command}: {description}")
    print('\n')


async def send_commands(websocket):
    """
    Asynchronously read user input and send it over the WebSocket.
    """
    try:
        while True:
            command = await aioconsole.ainput('sim command > ')

            if command == 'help':
                await show_help()
            elif command == 'start':
                await websocket.send(command)
            elif command == 'pause':
                await websocket.send(command)
            elif command == 'resume':
                await websocket.send(command)
            elif command == 'shutdown':
                await websocket.send(command)
            elif command == 'exit':
                return
            else:
                await show_help(cmd=command)

    except websockets.ConnectionClosed:
        print("WebSocket connection closed")
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Error: {e}")


async def main(host: str = 'localhost', port: int = '1234'):
    """
    Connects to the websocket and then sends commands from the user as simulation events.
    """
    uri = f"ws://{host}:{port}"
    max_retries = 10
    retry_count = 0

    while retry_count < max_retries:
        try:
            async with websockets.connect(uri) as websocket:
                print(f"Connected to {uri}")
                tasks = [
                    asyncio.create_task(send_commands(websocket)),
                    asyncio.create_task(websocket.wait_closed())
                ]
                done, pending = await asyncio.wait(
                    tasks,
                    return_when=asyncio.FIRST_COMPLETED
                )
                for task in pending:
                    task.cancel()
                print("Connection closed")
                return  # Exit the function after successful communication
        except Exception as e:
            retry_count += 1
            print(f"Connection failed ({retry_count}/{max_retries}): {e}")
            if retry_count < max_retries:
                print("Retrying in 3 seconds...")
                await asyncio.sleep(3)
            else:
                print("Max retries reached. Exiting.")
                return


if __name__ == '__main__':
    # Parse command-line arguments with defaults
    parser = argparse.ArgumentParser(description='Connect to a WebSocket and send commands.')
    parser.add_argument('--host', default='localhost', help='WebSocket host (default: localhost)')
    parser.add_argument('--port', type=int, default=1234, help='WebSocket port (default: 1234)')
    args = parser.parse_args()

    try:
        asyncio.run(main(args.host, args.port))
    except KeyboardInterrupt:
        print('^C received, shutting down the CLI.')
