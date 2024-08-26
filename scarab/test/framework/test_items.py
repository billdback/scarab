from dataclasses import dataclass

from scarab.framework.entity import Entity, entity_created, entity_updated, entity_destroyed, simulation_start, \
    simulation_pause, simulation_resume, simulation_shutdown, time_updated, event
from scarab.framework.events import EntityCreatedEvent, Event, ScarabEventType, EntityUpdatedEvent, \
    EntityDestroyedEvent, \
    SimulationStartEvent, SimulationPauseEvent, SimulationResumeEvent, SimulationShutdownEvent, TimeUpdatedEvent


@Entity(name="test1")
class TestEntity1:
    """Entity to use for testing."""

    def __init__(self, prop1: str = "", prop2: int = 0):
        """Creates a new test entity with a couple optional props for testing."""
        self.prop1 = prop1
        self.prop2 = prop2

        self.nbr_test2_entities = 0
        self.test_entity_2 = None

        self.simulation_running = False
        self.simulation_time = 0

        self.nbr_generic_events = 0

    @entity_created(entity_name='test2')
    def entity_2_created(self, ce: EntityCreatedEvent):
        """Called when a new test2 class was created."""
        assert ce.event_name == ScarabEventType.ENTITY_CREATED
        assert ce.entity.scarab_name == 'test2'
        self.nbr_test2_entities += 1
        self.test_entity_2 = ce.entity

    @entity_updated(entity_name='test2')
    def entity_2_updated(self, ue: EntityUpdatedEvent):
        """Called with a test2 entity is updated."""
        self.test_entity_2 = ue.entity

    @entity_destroyed(entity_name='test2')
    def entity_2_destroyed(self, de: EntityDestroyedEvent):
        """Called when a test2 entity was destroyed."""
        self.test_entity_2 = None
        self.nbr_test2_entities -= 1

    @simulation_start()
    def simulation_start(self, se: SimulationStartEvent):
        """Called when the simulation starts."""
        self.simulation_running = True

    @simulation_pause()
    def simulation_pause(self, se: SimulationPauseEvent):
        """Called when the simulation starts."""
        self.simulation_running = False

    @simulation_resume()
    def simulation_resume(self, se: SimulationResumeEvent):
        """Called when the simulation resumes."""
        self.simulation_running = True

    @simulation_shutdown()
    def simulation_shutdown(self, se: SimulationShutdownEvent):
        """Called when the simulation is shutting down."""
        self.simulation_running = False

    @time_updated()
    def time_updated(self, tue: TimeUpdatedEvent):
        """Called when time updates."""
        self.simulation_time = tue.sim_time

    @event(name='generic')
    def handle_generic(self, evt: Event):
        """Called when a generic event is sent."""
        self.nbr_generic_events += 1


@dataclass
class Test2EntityType:
    prop3: str = ""
    prop4: int = 0


@Entity(name="test2", conforms_to=Test2EntityType)
class TestEntity2:
    """Entity to use for testing that conforms."""

    def __init__(self, prop3: str = "", prop4: int = 0):
        """Creates a new test entity with a couple optional props for testing."""
        self.prop3 = prop3
        self.prop4 = prop4

        self.prop5 = True  # not in the type, but should be OK
