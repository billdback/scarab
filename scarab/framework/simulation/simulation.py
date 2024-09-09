"""
The actual simulation class.
"""
from enum import StrEnum
import logging
import time
from typing import Dict, List
import uuid

from ._event_queue import OrderedEventQueue
from ._event_router import EventRouter

from scarab.framework.entity import Entity, scarab_properties
from scarab.framework.events import Event, EntityCreatedEvent, EntityDestroyedEvent, EntityChangedEvent, \
    ScarabEventType, TimeUpdatedEvent, \
    SimulationStartEvent, SimulationPauseEvent, SimulationResumeEvent, SimulationShutdownEvent

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger.setLevel(logging.INFO)

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

    def __init__(self):
        """
        Creates a new simulation.
        """
        self._current_state = SimulationState.paused
        self._current_time = 0
        self._run_to = -1  # used to determine how long to run.

        self._entities: Dict[SimID, Entity] = {}

        self._event_queue = OrderedEventQueue()
        self._event_router = EventRouter()

    @property
    def state(self) -> SimulationState:
        """Returns the current state of the simulation"""
        return self._current_state

    def run(self, nbr_steps=None, cycle_length=0) -> None:
        """
        Runs the simulation for the number of steps (or until there are no more events in the queue).
        :param nbr_steps: If provided (i.e. positive number), will only run this many steps and then pause.
        :param cycle_length: The (approximate) length of a given step in seconds.  It may not be exact.
        """
        if nbr_steps <= 0:
            logger.warning(f"Attempting to run negative or zero steps: {nbr_steps}")
            return

        if nbr_steps:
            self._run_to = self._current_time + nbr_steps

        if self._current_state == SimulationState.shutting_down:
            raise RuntimeError(f"Attempting to run a simulation after shutdown.")

        if self._current_time == 0:  # just starting for the first time.
            self._event_router.route(SimulationStartEvent(sim_time=self._current_time))
        else:  # must be resuming
            self.resume()

        # told to run, so set the state.
        self._current_state = SimulationState.running

        # run until there's no more time to run.  This locks down the main thread.
        # TODO consider if we should auto shutdown or pause if out of events.
        while self._current_state != SimulationState.shutting_down:
            # It's possible to pause the simulation while running.
            if self._current_state == SimulationState.running:
                # None indicates to keep running indefinitely.  Else just run to the desired time.
                if self._run_to == -1 or (self._current_time < self._run_to):

                    # Steps will be up to a minimum of the step time.
                    self._current_time += 1  # increment to the next time interval.
                    cycle_start_time = time.time()

                    self._step()  # do the interval.

                    cycle_end_time = time.time()
                    execution_time = cycle_end_time - cycle_start_time
                    if execution_time < cycle_length:
                        time.sleep(cycle_length - execution_time)

                # if not indefinite, see if we've reached the pause time.  Also want to return in these cases vs. just
                # getting a command to pause.
                elif self._run_to != -1 and self._current_time == self._run_to:
                    self.pause()
                    return
            else:  # currently paused, so wait a second and see if we should restart.
                time.sleep(1)

    def _step(self) -> None:
        """
        Steps the simulation one time.
        """
        # Order of events is time updated, then stuff from the queue.  Note that
        # simulation events are sent when they occur.

        # FUTURE For now just incrementing by 1, but could change in the future.
        self._event_router.route(TimeUpdatedEvent(sim_time=self._current_time, previous_time=self._current_time - 1))
        before_event_properties = self._get_before_entity_properties()
        while self._current_time == self._event_queue.next_event_time:
            event = self._event_queue.next_event()
            self._event_router.route(event)
        self._send_entity_change_events(before_event_properties)

    def _get_before_entity_properties(self) -> Dict[SimID, Dict[str, object]]:
        """
        Gets the properties prior to a step to be compared for entity update messages.  This should only be called
        from the _step method.
        :return: A dictionary that has the entity ID and the properties before the step.
        """
        before_properties = {}
        for entity in self._entities.values():
            before_properties[entity.scarab_id] = scarab_properties(entity)

        return before_properties

    def _send_entity_change_events(self, before_properties: Dict[SimID, Dict[str, object]]) -> None:
        """
        Sends the entity change events.  This should only be called by the _step method.
        :param before_properties: The properties before the latest step.  The will be compared with current state to see
        what changed and then update events will be queued..
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

    def pause(self) -> None:
        """
        Causes the simulation to pause.
        """
        self._event_router.route(SimulationPauseEvent(sim_time=self._current_time))
        self._current_state = SimulationState.paused

    def resume(self) -> None:
        """
        Causes the simulation to resume.
        """
        self._event_router.route(SimulationResumeEvent(sim_time=self._current_time))
        self._current_state = SimulationState.running

    def shutdown(self) -> None:
        """
        Causes the simulation to shut down.
        """
        self._event_router.route(SimulationShutdownEvent(sim_time=self._current_time))
        self._current_state = SimulationState.shutting_down

    #####################################   Entity and event handling.  #####################################

    _immediate_events = [ScarabEventType.SIMULATION_START, ScarabEventType.SIMULATION_PAUSE,
                         ScarabEventType.SIMULATION_RESUME, ScarabEventType.SIMULATION_SHUTDOWN,
                         ScarabEventType.TIME_UPDATED]

    def send_event(self, event: Event) -> None:
        """
        Sends an event to interested entity based on their declarations.  Time updated and simulation events are sent
        immediately.  All other events are sent at the next time.
        :param Event:  The event to send.
        """
        if event.event_name in Simulation._immediate_events:
            event.sim_time = self._current_time
            self._event_router.route(event)

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
