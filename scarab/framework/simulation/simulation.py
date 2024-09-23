"""
Copyright (c) 2024 William D Back

This file is part of Scarab licensed under the MIT License.
For full license text, see the LICENSE file in the project root.

The actual simulation class.
"""
import asyncio
from datetime import datetime
from enum import StrEnum
import logging
import time
from typing import Dict, List
import uuid

from ._event_queue import OrderedEventQueue
from ._event_router import EventRouter
from ._ws_server import WSEventServer

from ..entity import Entity, scarab_properties
from ..events import Event, EntityCreatedEvent, EntityDestroyedEvent, EntityChangedEvent, \
    ScarabEventType, TimeUpdatedEvent, \
    SimulationStartEvent, SimulationPauseEvent, SimulationResumeEvent, SimulationShutdownEvent

from ..event_loggers import BaseLogger, FileLogger

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger.setLevel(logging.ERROR)

SimID = str


def new_sim_id() -> SimID:
    """Returns a new simulation ID"""
    return str(uuid.uuid4())


class SimulationState(StrEnum):
    """The current state of the simulation"""
    paused = 'paused'
    running = 'running'
    shutting_down = 'shutting_down'


class Simulation:
    """
    Simulation class for managing entities and events.
    """

    def __init__(self, event_logger: BaseLogger = None, ws_host: str = 'localhost', ws_port: int = 1234):
        """
        Creates a new simulation.
        :param event_logger: The logger to use if any.  If not provided, a default file logger will be used
        that consists of the datetime in the current location.
        :param ws_host: The host for the websocket server.
        :param ws_port: The port for the websocket server.
        """

        # Track state including changes.
        self._current_state = SimulationState.paused
        self._previous_state = self._current_state

        self._current_time = 0
        self._run_to = -1  # used to determine how long to run.

        self._ws_server = WSEventServer(sim=self, host=ws_host, port=ws_port)

        # Technically has entities, but entities are simply objects with scarab_ properties.
        self._entities: Dict[SimID, object] = {}

        self._event_queue = OrderedEventQueue()

        if event_logger is None:
            # default to a file logger that logs all events.
            event_logger = FileLogger(datetime.now().strftime("%Y.%m.%d-%H.%M.log"))

        self._event_router = EventRouter(event_logger, self._ws_server)

    @property
    def state(self) -> SimulationState:
        """Returns the current state of the simulation"""
        return self._current_state

    def __enter__(self):
        """
        Context manager for the simulation.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Ends the context, making sure the shutdown message is sent and the web socket server is closed.
        """

        logger.debug(f"Shutting down via exit")

        # the main loop should be done at this point.
        try:
            asyncio.run(self._event_router.route(SimulationShutdownEvent(sim_time=self._current_time)))
            asyncio.run(self._ws_server.stop_server())
            logger.debug(f"called stop_server")
        except RuntimeError as e:
            logger.debug(e)
            pass

    def run(self, nbr_steps: int = None, step_length: int = 0, start_paused: bool = False) -> None:
        """
        Runs the simulation for the number of steps (or until there are no more events in the queue).
        :param nbr_steps: If provided (i.e. positive number), will only run this many steps and then shutdown.
        :param step_length: The (approximate) length of a given step in seconds.  It may not be exact.
        :param start_paused: If True, the run loop will start, but the simulation will be paused and wait for an event
        to run.
        """
        asyncio.run(self._run(nbr_steps, step_length, start_paused))

    async def _run(self, nbr_steps: int = None, step_length: int = 0, start_paused: bool = False) -> None:
        """
        Kicks off the simulation and the socket server.
        :param nbr_steps: If provided (i.e. positive number), will only run this many steps and then shutdown.
        :param step_length: The (approximate) length of a given step in seconds.  It may not be exact.
        :param start_paused: If True, the run loop will start, but the simulation will be paused and wait for an event
        to run.
        """

        await self._ws_server.start_server()

        await self._run_steps(nbr_steps, step_length, start_paused)
        await self._ws_server.stop_server()

    async def _run_steps(self, nbr_steps: int = None, step_length: int = 0, start_paused: bool = False) -> None:
        """
        Runs the simulation for the number of steps (or until there are no more events in the queue).
        :param nbr_steps: If provided (i.e. positive number), will only run this many steps and then shutdown.
        :param step_length: The (approximate) length of a given step in seconds.  It may not be exact.
        :param start_paused: If True, the run loop will start, but the simulation will be paused and wait for an event
        to run.
        """
        logger.info(f'running simulation {nbr_steps} steps')
        if nbr_steps and nbr_steps <= 0:
            logger.error(f"Attempting to run negative or zero steps: {nbr_steps}")
            return

        if nbr_steps:
            self._run_to = self._current_time + nbr_steps

        if self._current_state == SimulationState.shutting_down:
            raise RuntimeError(f"Attempting to run a simulation after shutdown.")

        self._current_state = SimulationState.paused if start_paused else SimulationState.running

        # The simulation can start running in a paused state, which means that it's ready to run, but waiting for a
        # command.  This is useful for scenarios where the controller is an external app.  Note that if nothing
        # ever starts the simulation, it will be looping forever.
        if start_paused:
            await self._route_event(SimulationPauseEvent(sim_time=self._current_time))
        else:
            if self._current_time == 0:  # just starting for the first time.
                await self._route_event(SimulationStartEvent(sim_time=self._current_time))
            else:  # must be resuming - changes will be caught below.
                pass

        # Run until there's no more time to run and then shutdown.  This locks down the main thread.
        while self._current_state != SimulationState.shutting_down:
            await asyncio.sleep(0.001)  # Allow other processes to run without adding a significant delay.

            # see if the state changed and send messages as needed.
            await self._check_state_change()

            # It's possible to pause the simulation while running.
            if self._current_state == SimulationState.running:
                # None indicates to keep running indefinitely.  Else just run to the desired time.
                if self._run_to == -1 or (self._current_time < self._run_to):

                    # Steps will be up to a minimum of the step time.
                    self._current_time += 1  # increment to the next time interval.
                    cycle_start_time = time.time()

                    await self._step()  # do the interval.

                    cycle_end_time = time.time()
                    execution_time = cycle_end_time - cycle_start_time
                    if execution_time < step_length:
                        await asyncio.sleep(step_length - execution_time)

                # if not indefinite, see if we've reached the pause time.
                elif self._run_to != -1 and self._current_time == self._run_to:
                    self.pause()
                    # the event has to be sent here since we are returning.
                    await self._event_router.route(SimulationPauseEvent(sim_time=self._current_time))
                    return  # need to return to main thread
            else:  # currently paused, so wait a second and see if we should restart.
                await asyncio.sleep(1)

        # let everyone know we are going by-by.
        await self._event_router.route(SimulationShutdownEvent(sim_time=self._current_time))

    async def _route_event(self, event: Event) -> None:
        """
        Routes the message, making sure it's handled as a synchronized send.
        :param event: The event to route.
        """
        logger.debug(f"Simulation is routing event: {event.to_json()}")
        await self._event_router.route(event=event)

    async def _check_state_change(self) -> None:
        """
        Checks to see if the current state and previous state are different.  If so, send an appropriate event.
        """
        if self._previous_state == self._current_state:
            return  # no changes

        # Main state changes.  May need to capture others later.
        if self._previous_state == SimulationState.running and self._current_state == SimulationState.paused:
            await self._route_event(SimulationPauseEvent(sim_time=self._current_time))
        elif self._previous_state == SimulationState.paused and self._current_state == SimulationState.running:
            await self._route_event(SimulationResumeEvent(sim_time=self._current_time))

        # set the previous to current now that it's been checked.
        self._previous_state = self._current_state

    async def _step(self) -> None:
        """
        Steps the simulation one time.
        """
        # Order of events is time updated, then stuff from the queue.  Note that
        # simulation events are sent when they occur.

        logger.info(f"Simulation stepping at time {self._current_time}")

        # FUTURE For now just incrementing by 1, but could change in the future.
        await self._route_event(
            TimeUpdatedEvent(sim_time=self._current_time, previous_time=self._current_time - 1))
        before_event_properties = self._get_before_entity_properties()
        while self._current_time == self._event_queue.next_event_time:
            event = self._event_queue.next_event()
            print(event.to_json())
            await self._route_event(event)
        await self._send_entity_change_events(before_event_properties)

    def _get_before_entity_properties(self) -> Dict[SimID, Dict[str, object]]:
        """
        Gets the properties prior to a step to be compared for entity update messages.  This should only be called
        from the _step method.
        :return: A dictionary that has the entity ID and the properties before the step.
        """
        before_properties = {}
        for entity in self._entities.values():
            before_properties[getattr(entity, 'scarab_id')] = scarab_properties(entity)

        return before_properties

    async def _send_entity_change_events(self, before_properties: Dict[SimID, Dict[str, object]]) -> None:
        """
        Sends the entity change events.  This should only be called by the _step method.
        :param before_properties: The properties before the latest step.  This will be compared with current state to
        see what changed and then update events will be queued.
        """
        for entityID, old_properties in before_properties.items():
            entity = self._entities.get(entityID, None)  # it might be possible to not get an entity if it was deleted
            if entity:
                new_properties = scarab_properties(entity)
                changed_properties = self._compare_properties(old_properties, new_properties)
                if len(changed_properties) > 0:
                    self.send_event(EntityChangedEvent(scarab_properties(entity), changed_properties))

    @classmethod
    def _compare_properties(cls, old_properties: Dict[str, object], new_properties: Dict[str, object]) -> List[str]:
        """
        Returns a list of properties that changed between the old and new properties.  There are three changes types:
        1. New properties are added.
        2. Old properties are deleted.
        3. Existing property values are changed.
        :param old_properties: The list of old properties.
        :param new_properties: The list of new properties.
        """
        changed_properties = []
        for prop_name, prop_value in new_properties.items():
            if prop_name in old_properties:  # changed
                if old_properties[prop_name] != prop_value:
                    changed_properties.append(prop_name)
            else:  # new
                changed_properties.append(prop_name)
        for prop_name in old_properties:  # deleted
            if prop_name not in new_properties:
                changed_properties.append(prop_name)

        return changed_properties

    # TODO for the pause, resume, and shutdown, have these set the state and then the _run will handle the
    #  state change and send the event.

    def pause(self) -> None:
        """
        Causes the simulation to pause.
        """
        self._current_state = SimulationState.paused

    def resume(self) -> None:
        """
        Causes the simulation to resume.
        """
        self._current_state = SimulationState.running

    def shutdown(self) -> None:
        """
        Causes the simulation to shut down.
        """
        self._current_state = SimulationState.shutting_down

    # ####################################   Entity and event handling.  #####################################

    _immediate_events = [ScarabEventType.SIMULATION_START, ScarabEventType.SIMULATION_PAUSE,
                         ScarabEventType.SIMULATION_RESUME, ScarabEventType.SIMULATION_SHUTDOWN,
                         ScarabEventType.TIME_UPDATED]

    def send_event(self, event: Event) -> None:
        """
        Sends an event to interested entity based on their declarations.  Time updated and simulation events are sent
        immediately.  All other events are sent at the next time.
        :param event:  The event to send.
        """
        if event.event_name in Simulation._immediate_events:
            event.sim_time = self._current_time
            self._route_event(event)

        else:
            # If there is no sim time provided, send in the next cycle.
            if event.sim_time is None:
                event.sim_time = self._current_time + 1
            self._event_queue.put(event)

    def add_entity(self, entity: object) -> None:
        """
        Adds the entity to the simulation.  An ID will be assigned to the entity, potentially overwriting an existing
        one.
        :param entity: The entity to add.  Entities can technically be any class, but will have the scarab attributes.
        """
        assert hasattr(entity, "scarab_id")  # basic check that this is an entity.

        logger.debug(f'Adding entity: {entity}')

        entity.scarab_id = new_sim_id()
        self._entities[entity.scarab_id] = entity
        self._event_router.register(entity=entity)
        self.send_event(EntityCreatedEvent(entity_props=scarab_properties(entity)))

    def destroy_entity(self, entity: Entity) -> None:
        """
        Destroys the entity.  The entity is unique based on the simID.
        :param entity: The entity to destroy.
        """
        if entity.scarab_id not in self._entities:
            logger.warning(f"Attempting to delete entity {scarab_properties(entity)} with unknown ID")
            return  # not known, so delete.

        del self._entities[entity.scarab_id]
        self._event_router.unregister(entity=entity)
        self.send_event(EntityDestroyedEvent(scarab_properties(entity)))
