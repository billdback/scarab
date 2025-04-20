"""
Copyright (c) 2024 William D Back

This file is part of Scarab licensed under the MIT License.
For full license text, see the LICENSE file in the project root.

This file contains classes and types for working with entities.
"""
import dataclasses
from dataclasses import asdict
import functools
from typing import Generic, Type, TypeVar

from scarab.framework.events import *
from scarab.framework.types import ScarabException

T = TypeVar('T')
P = TypeVar('P')


class EntityWrapper(Generic[T]):
    """
    Wrapper for a class with a name to use in the simulation.  This allows you to easily swap out
    implementation classes. e.g.
    @Entity(name="Bee")
    class.....

    The component returns a new type with common attributes and methods that can be used by the framework.  Simulation
    developers should _not_ be using the internal details.
    """

    def __init__(self, cls: Type[T], name: str, conforms_to=None):
        """
        Creates a new entity decorator with the given name.
        """
        if not name:
            raise ScarabException("No name provided for entity")
        if conforms_to and not dataclasses.is_dataclass(conforms_to):
            raise ScarabException(f'"conforms_to" must be a dataclass.  Provided type: {conforms_to}')

        self.cls = cls
        self.scarab_id = None
        self.scarab_name = name
        self.scarab_conforms_to = conforms_to.__new__(conforms_to) if conforms_to else None

    def __call__(self, *args, **kwargs):
        instance = self.cls(*args, **kwargs)
        instance.scarab_id = self.scarab_id
        instance.scarab_name = self.scarab_name
        instance.scarab_conforms_to = self.scarab_conforms_to

        # Add send_event method to the instance
        def send_event(self, event):
            """
            Sends an event to the simulation.
            :param event: The event to send.
            """
            if hasattr(self, 'scarab_simulation'):
                # Set the sender_id of the event to this entity's ID
                event.sender_id = self.scarab_id
                self.scarab_simulation.send_event(event)
            else:
                raise AttributeError(
                    "Entity not added to a simulation yet. Add the entity to a simulation before sending events.")

        instance.send_event = send_event.__get__(instance)

        # Add send_command method to the instance
        def send_command(self, event, scarab_id):
            """
            Sends a command (targeted event) to a specific entity.
            :param event: The event to send.
            :param scarab_id: The ID of the target entity.
            """
            if hasattr(self, 'scarab_simulation'):
                # Set the target_id and sender_id of the event
                event.target_id = scarab_id
                event.sender_id = self.scarab_id
                self.scarab_simulation.send_event(event)
            else:
                raise AttributeError(
                    "Entity not added to a simulation yet. Add the entity to a simulation before sending commands.")

        instance.send_command = send_command.__get__(instance)

        self._scarab_does_conform(instance)

        return instance

    def _scarab_does_conform(self, instance) -> bool:
        """
        Checks if the instance conforms to the data type it says it does.
        :param instance: The instance (of an Entity) to check.
        :return bool: True if the instance conforms.
        """
        # optionally can ignore the conforming rules.
        if not self.scarab_conforms_to:
            return True

        missing_properties = []
        conforming_properties = asdict(self.scarab_conforms_to).keys()
        for p in conforming_properties:
            if p not in instance.__dict__:
                missing_properties.append(p)

        if missing_properties:
            raise ScarabException(f'Entity missing properties: {", ".join(missing_properties)}')

        return True


def scarab_properties(obj) -> Dict[str, object]:
    """
    Returns a list of the properties for a scarab entity, including the name and id as a dictionary.
    """

    props = {
        'scarab_name': obj.scarab_name,
        'scarab_id': obj.scarab_id
    }

    # If the entity conforms with a type, only the conforming values are passed.
    if obj.scarab_conforms_to:
        for p in dataclasses.asdict(obj.scarab_conforms_to).keys():
            # The existence of the prop should have been already check, so get the value from the object.
            props[p] = getattr(obj, p)

    # if not conforming, then all public properties are added.
    else:
        for p, v in obj.__dict__.items():
            if not p.startswith("_"):
                props[p] = v

    return props


"""
class Entity(EntityWrapper[T]):

    def __init__(self, name: str, cls: Type[T], conforms_to=None):
        super().__init__(cls, name, conforms_to)
        self.scarab_name = name
        self.scarab_conforms_to = conforms_to

    def __call__(self, cls):
        super(Entity, self).__init__(cls, self.scarab_name, self.scarab_conforms_to)

        def wrapper(*args, **kwargs):
            instance = super(Entity, self).__call__(*args, **kwargs)
            return instance

        return wrapper
"""


class Entity(Generic[T]):
    """
    Decorator class to create an EntityWrapper for the decorated class.
    """

    def __init__(self, name: str, conforms_to=None):
        self.name = name
        self.conforms_to = conforms_to

    def __call__(self, cls: Type[T]) -> EntityWrapper[T]:
        return EntityWrapper(cls, self.name, self.conforms_to)


"""
Event handler decorators to signify a function handles a specific event.  This simply decorates the method and then
when the entity is added to the simulation, the simulation will introspect the class and add the handler for messages.
"""


class ScarabEventHandler:
    """Based event handler for all scarab event handlers."""


class entity_created(ScarabEventHandler):
    """
    Decorator for methods that handle entity created events.

    @entity_created(entity_name='some-entity')
    handle_entity_created(self, ce: EntityCreatedEvent)
        pass
    """

    def __init__(self, entity_name: str):
        """
        Create a new wrapper for create handlers for a given name.
        :param entity_name: Name of the entity to handle.
        """
        super().__init__()
        self.entity_name = entity_name

    def __call__(self, func):
        """
        Invokes the function, passing the entity created event.
        """

        @functools.wraps(func)
        def wrapper(instance, *local_args, **local_kwargs):
            return func(instance, *local_args, **local_kwargs)

        wrapper.scarab_handler = True
        wrapper.event_type = ScarabEventType.ENTITY_CREATED
        wrapper.entity_name = self.entity_name

        return wrapper


class entity_changed(ScarabEventHandler):
    """
    Decorator for methods that handle entity updated events.

    @entity_updated(entity_name='some-entity')
    handle_entity_created(self, ce: EntityUpdatedEvent)
        pass
    """

    def __init__(self, entity_name: str):
        """
        Create a new wrapper for entity updated events.
        :param entity_name: Name of the entity to handle.
        """
        super().__init__()
        self.entity_name = entity_name

    def __call__(self, func):
        """
        Invokes the function, passing the entity updated event.
        """

        @functools.wraps(func)
        def wrapper(instance, *local_args, **local_kwargs):
            return func(instance, *local_args, **local_kwargs)

        wrapper.scarab_handler = True
        wrapper.event_type = ScarabEventType.ENTITY_CHANGED
        wrapper.entity_name = self.entity_name

        return wrapper


class entity_destroyed(ScarabEventHandler):
    """
    Decorator for methods that handle entity destroyed events.

    @entity_destroyed(entity_name='some-entity')
    handle_entity_destroyed(self, ce: EntityUpdatedEvent)
        pass
    """

    def __init__(self, entity_name: str):
        """
        Create a new wrapper for create handlers for an entity.
        :param entity_name: Name of the entity that was destroyed.
        """
        super().__init__()
        self.entity_name = entity_name

    def __call__(self, func):
        """
        Invokes the function, passing the entity destroyed event.
        """

        @functools.wraps(func)
        def wrapper(instance, *local_args, **local_kwargs):
            return func(instance, *local_args, **local_kwargs)

        wrapper.scarab_handler = True
        wrapper.event_type = ScarabEventType.ENTITY_DESTROYED
        wrapper.entity_name = self.entity_name

        return wrapper


class simulation_start(ScarabEventHandler):
    """
    Decorator for methods that handle simulation start events.

    @simulation_start()
    handle_simulation_start(self, ce: SimulationStartEvent)
        pass
    """

    def __init__(self):
        """
        Create a new wrapper for handling simulation start events
        """
        super().__init__()

    def __call__(self, func):
        """
        Invokes the function, passing the simulation start event.
        """

        @functools.wraps(func)
        def wrapper(instance, *local_args, **local_kwargs):
            return func(instance, *local_args, **local_kwargs)

        wrapper.scarab_handler = True
        wrapper.event_type = ScarabEventType.SIMULATION_START

        return wrapper


class simulation_pause(ScarabEventHandler):
    """
    Decorator for methods that handle simulation pause events.

    @simulation_pause()
    handle_simulation_pause(self, ce: SimulationPauseEvent)
        pass
    """

    def __init__(self):
        """
        Create a new wrapper for handling simulation pause events.
        """
        super().__init__()

    def __call__(self, func):
        """
        Invokes the function.
        """

        @functools.wraps(func)
        def wrapper(instance, *local_args, **local_kwargs):
            return func(instance, *local_args, **local_kwargs)

        wrapper.scarab_handler = True
        wrapper.event_type = ScarabEventType.SIMULATION_PAUSE

        return wrapper


class simulation_resume(ScarabEventHandler):
    """
    Decorator for methods that handle simulation resume events.

    @simulation_resume()
    handle_simulation_resume(self, ce: SimulationResumeEvent)
        pass
    """

    def __init__(self):
        """
        Create a new wrapper for handling simulation resume events.
        """
        super().__init__()

    def __call__(self, func):
        """
        Invokes the function.
        """

        @functools.wraps(func)
        def wrapper(instance, *local_args, **local_kwargs):
            return func(instance, *local_args, **local_kwargs)

        wrapper.scarab_handler = True
        wrapper.event_type = ScarabEventType.SIMULATION_RESUME

        return wrapper


class simulation_shutdown(ScarabEventHandler):
    """
    Decorator for methods that handle simulation shutdown events.

    @simulation_shutdown()
    handle_simulation_shutdown(self, ce: SimulationShutdown)
        pass
    """

    def __init__(self):
        """
        Create a new wrapper for handling simulation shutdown events.
        """
        super().__init__()

    def __call__(self, func):
        """
        Invokes the function.
        """

        @functools.wraps(func)
        def wrapper(instance, *local_args, **local_kwargs):
            return func(instance, *local_args, **local_kwargs)

        wrapper.scarab_handler = True
        wrapper.event_type = ScarabEventType.SIMULATION_SHUTDOWN

        return wrapper


class time_updated(ScarabEventHandler):
    """
    Decorator for methods that handle simulation time updated events.

    @time_updated()
    handle_simulation_time_updated(self, ce: SimulationTimeUpdated)
        pass
    """

    def __init__(self):
        """
        Create a new wrapper for handling time updates.
        """
        super().__init__()

    def __call__(self, func):
        """
        Invokes the function.
        """

        @functools.wraps(func)
        def wrapper(instance, *local_args, **local_kwargs):
            return func(instance, *local_args, **local_kwargs)

        wrapper.scarab_handler = True
        wrapper.event_type = ScarabEventType.TIME_UPDATED

        return wrapper


class event(ScarabEventHandler):
    """
    Decorator for methods that handle events based on the event name.  Note that this _cannot_ be used for
    standard Scarab events, such as entity_created.

    @event(name='my-event')
    handle_my_event(self, evt: Event)
        pass
    """

    def __init__(self, name: str):
        """
        Create a new wrapper for named events.
        :param name: Name of the event to handle.
        """
        super().__init__()
        self.event_name = name

    def __call__(self, func):
        """
        Invokes the function, passing the entity updated event.
        """

        @functools.wraps(func)
        def wrapper(instance, *local_args, **local_kwargs):
            return func(instance, *local_args, **local_kwargs)

        wrapper.scarab_handler = True
        wrapper.event_type = ScarabEventType.NAMED_EVENT
        wrapper.event_name = self.event_name

        return wrapper
