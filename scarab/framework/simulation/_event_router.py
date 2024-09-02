"""
Event router for routing events to the appropriate entity handlers.
"""

from collections import namedtuple
import inspect
import logging
from typing import Dict, List

from scarab.framework.types import EventHandler
from scarab.framework.events import Event, ScarabEventType

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

EntityAndHandler = namedtuple('EntityAndHandler', ['entity', 'handler'])


class EventRouter:
    """
    The event router allows entities to be registered with the event router.  The router will introspect the entities
    to find their handlers and then add them.  The router can then accept mesages and route them to the correct
    entities.  Finally, entities can be removed.
    """

    def __init__(self):
        """
        Create a new EventRouter that will have the handlers for the entity.

        The router contains known lists for the standard event types, such as EntityCreatedEvent, EntityUpdatedEvent,
        etc.  Then there are event routers with the name of the event, to account for general events.

        Each event type varies in how it stores the handlers.  For ones that are specific to entities, such as
        EntityCreatedEvent, the router stores in a dictionary based on the entity name (str).  Then the list contains
        the entity and handler to call.  This allows the router to invoke the method on the instance.  It also makes it
        possible to easily delete the entity when it's destroyed.
        """

        # Entity related events.
        self._entity_created_handlers: Dict[str, List[EntityAndHandler]] = {}  # entity type -> EntityAndHandler tuple.
        self._entity_changed_handlers: Dict[str, List[EntityAndHandler]] = {}  # entity type -> EntityAndHandler tuple.
        self._entity_destroyed_handlers: Dict[
            str, List[EntityAndHandler]] = {}  # entity type -> EntityAndHandler tuple.

        # Simulation state change handlers.
        self._simulation_start_handlers: List[EntityAndHandler] = []
        self._simulation_pause_handlers: List[EntityAndHandler] = []
        self._simulation_resume_handlers: List[EntityAndHandler] = []
        self._simulation_shutdown_handlers: List[EntityAndHandler] = []

        # Time updated events.
        self._time_updated_handlers: List[EntityAndHandler] = []

        # Generic (named) events.
        self._named_event_handlers: Dict[str, List[EntityAndHandler]] = {}  # event name -> Entity and handler tuple.

    def register(self, entity: object) -> None:
        """
        Registers an entity with the router.  The router will search the entity for handlers and then register those
        to be called later.
        :param entity: The entity to register.  Entities are unique based on their IDs.
        """

        # Verify that this is an entity by seeing if it has a scarab_name.
        if not hasattr(entity, "scarab_name"):
            logger.error(f"{object} doesn't appear to be an entity.")
            return

        logger.info(f"Registering entity: {entity.scarab_name}")

        for attr_name in dir(entity):
            attr = getattr(entity, attr_name)
            if callable(attr) and hasattr(attr, "scarab_handler") and attr.scarab_handler:
                logger.info(f"\tAdding handler for class {entity.scarab_name}:  {attr.event_type}")

                # verify that the method takes a single Event.
                sig = inspect.signature(attr)
                if len(sig.parameters) != 1:
                    logger.error(f"\t{attr_name} has {len(sig.parameters)} params instead of 1")
                    continue  # sorry, not sorry

                fn_ok = True
                for name, param in sig.parameters.items():
                    # should only be one, just checking for an Event
                    if not (issubclass(param.annotation, Event)):
                        logger.error(
                            f"\t{attr_name} is the wrong type {param.annotation}.  It must be an Event or subclass.")
                        fn_ok = False

                if fn_ok:

                    # Based on the type, add it to the correct list.
                    if attr.event_type == ScarabEventType.ENTITY_CREATED:
                        self._register_entity_created_handler(entity_name_to_handle=attr.entity_name, entity=entity,
                                                              handler=attr)
                    elif attr.event_type == ScarabEventType.ENTITY_CHANGED:
                        self._register_entity_changed_handler(entity_name_to_handle=attr.entity_name, entity=entity,
                                                              handler=attr)
                    elif attr.event_type == ScarabEventType.ENTITY_DESTROYED:
                        self._register_entity_destroyed_handler(entity_name_to_handle=attr.entity_name, entity=entity,
                                                                handler=attr)
                    elif attr.event_type == ScarabEventType.SIMULATION_START:
                        self._register_simulation_start_handler(entity=entity, handler=attr)
                    elif attr.event_type == ScarabEventType.SIMULATION_PAUSE:
                        self._register_simulation_pause_handler(entity=entity, handler=attr)
                    elif attr.event_type == ScarabEventType.SIMULATION_RESUME:
                        self._register_simulation_resume_handler(entity=entity, handler=attr)
                    elif attr.event_type == ScarabEventType.SIMULATION_SHUTDOWN:
                        self._register_simulation_shutdown_handler(entity=entity, handler=attr)
                    elif attr.event_type == ScarabEventType.TIME_UPDATED:
                        self._register_time_updated_handler(entity=entity, handler=attr)
                    elif attr.event_type == ScarabEventType.NAMED_EVENT:
                        self._register_named_event_handler(event_name_to_handle=attr.event_name, entity=entity,
                                                           handler=attr)
                    else:
                        logger.info(f"\t{attr_name} not yet supported")

    def _register_entity_created_handler(self, entity_name_to_handle: str, entity: object,
                                         handler: EventHandler) -> None:
        """
        Adds the event handler for the entity with the given name.
        :param entity_name_to_handle: The name of the entity that the handler if to be called for.
        :param entity: The entity with the handler.
        :param handler: The event handler for the entity.
        """
        entity_handlers = self._entity_created_handlers.get(entity_name_to_handle, [])
        entity_handlers.append(EntityAndHandler(entity, handler))
        self._entity_created_handlers[entity_name_to_handle] = entity_handlers  # add back to make sure it exists.

    def _register_entity_changed_handler(self, entity_name_to_handle: str, entity: object,
                                         handler: EventHandler) -> None:
        """
        Adds the event handler for the entity with the given name.
        :param entity_name_to_handle: The name of the entity that the handler if to be called for.
        :param entity: The entity with the handler.
        :param handler: The event handler for the entity.
        """
        entity_handlers = self._entity_changed_handlers.get(entity_name_to_handle, [])
        entity_handlers.append(EntityAndHandler(entity, handler))
        self._entity_changed_handlers[entity_name_to_handle] = entity_handlers  # add back to make sure it exists.

    def _register_entity_destroyed_handler(self, entity_name_to_handle: str, entity: object,
                                           handler: EventHandler) -> None:
        """
        Adds the event handler for the entity with the given name.
        :param entity_name_to_handle: The name of the entity that the handler if to be called for.
        :param entity: The entity with the handler.
        :param handler: The event handler for the entity.
        """
        entity_handlers = self._entity_destroyed_handlers.get(entity_name_to_handle, [])
        entity_handlers.append(EntityAndHandler(entity, handler))
        self._entity_destroyed_handlers[entity_name_to_handle] = entity_handlers  # add back to make sure it exists.

    def _register_simulation_start_handler(self, entity: object, handler: EventHandler) -> None:
        """
        Adds the event handler for simulation start messages.
        :param entity: The entity with the handler.
        :param handler: The event handler for the entity.
        """
        self._simulation_start_handlers.append(EntityAndHandler(entity, handler))

    def _register_simulation_pause_handler(self, entity: object, handler: EventHandler) -> None:
        """
        Adds the event handler for simulation pause messages.
        :param entity: The entity with the handler.
        :param handler: The event handler for the entity.
        """
        self._simulation_pause_handlers.append(EntityAndHandler(entity, handler))

    def _register_simulation_resume_handler(self, entity: object, handler: EventHandler) -> None:
        """
        Adds the event handler for simulation resume messages.
        :param entity: The entity with the handler.
        :param handler: The event handler for the entity.
        """
        self._simulation_resume_handlers.append(EntityAndHandler(entity, handler))

    def _register_simulation_shutdown_handler(self, entity: object, handler: EventHandler) -> None:
        """
        Adds the event handler for simulation shutdown messages.
        :param entity: The entity with the handler.
        :param handler: The event handler for the entity.
        """
        self._simulation_shutdown_handlers.append(EntityAndHandler(entity, handler))

    def _register_time_updated_handler(self, entity: object, handler: EventHandler) -> None:
        """
        Adds the event handler for simulation time updated messages.
        :param entity: The entity with the handler.
        :param handler: The event handler for the entity.
        """
        self._time_updated_handlers.append(EntityAndHandler(entity, handler))

    def _register_named_event_handler(self, event_name_to_handle: str, entity: object, handler: EventHandler) -> None:
        """
        Adds the event handler for general events based on the event name.
        :param event_name_to_handle: The name of the event that the handler if to be called for.
        :param entity: The entity with the handler.
        :param handler: The event handler for the entity.
        """
        entity_handlers = self._named_event_handlers.get(event_name_to_handle, [])
        entity_handlers.append(EntityAndHandler(entity, handler))
        self._named_event_handlers[event_name_to_handle] = entity_handlers  # add back to make sure it exists.

    def unregister(self, entity: object) -> None:
        """
        Unregisters (removes) an entity by removing all references, so it won't be called in the future.
        Note that this process is a bit intensive depending on the number of entities and handlers.  There is an
        assumption that entities in the simulation won't be removed frequently and at high rates.
        :param entity: The entity to unregister.  Entities are unique based on their IDs.
        """

        # Basically have to go through every list and remove the handler for the given entity.
        # Perhaps it would be better to break these out, but the code is pretty small and has to iterate all lists.

        # Entity event handlers.
        self._entity_created_handlers = {key: [item for item in value if item.entity.scarab_id != entity.scarab_id] for
                                         key, value in self._entity_created_handlers.items()}
        self._entity_changed_handlers = {key: [item for item in value if item.entity.scarab_id != entity.scarab_id] for
                                         key, value in self._entity_changed_handlers.items()}
        self._entity_destroyed_handlers = {key: [item for item in value if item.entity.scarab_id != entity.scarab_id]
                                           for
                                           key, value in self._entity_destroyed_handlers.items()}

        # Simulation state change handlers.
        self._simulation_start_handlers = [entry for entry in self._simulation_start_handlers if
                                           entry.entity.scarab_id != entity.scarab_id]
        self._simulation_pause_handlers = [entry for entry in self._simulation_pause_handlers if
                                           entry.entity.scarab_id != entity.scarab_id]
        self._simulation_resume_handlers = [entry for entry in self._simulation_resume_handlers if
                                            entry.entity.scarab_id != entity.scarab_id]
        self._simulation_shutdown_handlers = [entry for entry in self._simulation_shutdown_handlers if
                                              entry.entity.scarab_id != entity.scarab_id]

        # Time updated events.
        self._time_updated_handlers = [entry for entry in self._time_updated_handlers if
                                       entry.entity.scarab_id != entity.scarab_id]

        # Generic (named) events.
        self._named_event_handlers = {key: [item for item in value if item.entity.scarab_id != entity.scarab_id] for
                                      key, value in self._named_event_handlers.items()}

    def route(self, event: Event) -> None:
        """
        Routes the events to all event handlers.
        :param event: The event to route.
        WARNING | FUTURE: There may be scenarios where a method and an attribute have the same names and handlers will fail to
        be registered.
        """

        if event.event_name == ScarabEventType.ENTITY_CREATED:
            self._handle_entity_created(event)
        elif event.event_name == ScarabEventType.ENTITY_CHANGED:
            self._handle_entity_updated(event)
        elif event.event_name == ScarabEventType.ENTITY_DESTROYED:
            self._handle_entity_destroyed(event)
        elif event.event_name == ScarabEventType.SIMULATION_START:
            self._handle_simulation_start(event)
        elif event.event_name == ScarabEventType.SIMULATION_PAUSE:
            self._handle_simulation_pause(event)
        elif event.event_name == ScarabEventType.SIMULATION_RESUME:
            self._handle_simulation_resume(event)
        elif event.event_name == ScarabEventType.SIMULATION_SHUTDOWN:
            self._handle_simulation_shutdown(event)
        elif event.event_name == ScarabEventType.TIME_UPDATED:
            self._handle_time_updated(event)
        else:
            self._handle_named_event(event)

    def _handle_entity_created(self, event: Event) -> None:
        """
        Handles entity created events.
        :param event: An entity created event.
        """
        assert event.event_name == ScarabEventType.ENTITY_CREATED

        # event handlers are stored by entity name of entity to be handled.
        event_handlers = self._entity_created_handlers.get(event.entity.scarab_name, [])
        for h in event_handlers:
            try:
                h.handler(event)
            except Exception as e:
                logger.error(f"Error handling event {event} for entity {h.entity}: {e}")

    def _handle_entity_updated(self, event: Event) -> None:
        """
        Handles entity updated events.
        :param event: An entity updated event.
        """
        assert event.event_name == ScarabEventType.ENTITY_CHANGED

        # event handlers are stored by entity name of entity to be handled.
        event_handlers = self._entity_changed_handlers.get(event.entity.scarab_name, [])
        for h in event_handlers:
            try:
                h.handler(event)
            except Exception as e:
                logger.error(f"Error handling event {event} for entity {h.entity}: {e}")

    def _handle_entity_destroyed(self, event: Event) -> None:
        """
        Handles entity destroyed events.
        :param event: An entity destroyed event.
        """
        assert event.event_name == ScarabEventType.ENTITY_DESTROYED

        # event handlers are stored by entity name of entity to be handled.
        event_handlers = self._entity_destroyed_handlers.get(event.entity.scarab_name, [])
        for h in event_handlers:
            try:
                h.handler(event)
            except Exception as e:
                logger.error(f"Error handling event {event} for entity {h.entity}: {e}")

    def _handle_simulation_start(self, event: Event) -> None:
        """
        Handles simulation start events.
        :param event: A simulation start event.
        """
        assert event.event_name == ScarabEventType.SIMULATION_START

        for h in self._simulation_start_handlers:
            try:
                h.handler(event)
            except Exception as e:
                logger.error(f"Error handling event {event} for entity {h.entity}: {e}")

    def _handle_simulation_pause(self, event: Event) -> None:
        """
        Handles simulation pause events.
        :param event: A simulation pause event.
        """
        assert event.event_name == ScarabEventType.SIMULATION_PAUSE

        for h in self._simulation_pause_handlers:
            try:
                h.handler(event)
            except Exception as e:
                logger.error(f"Error handling event {event} for entity {h.entity}: {e}")

    def _handle_simulation_resume(self, event: Event) -> None:
        """
        Handles simulation resume events.
        :param event: A simulation resume event.
        """
        assert event.event_name == ScarabEventType.SIMULATION_RESUME

        for h in self._simulation_resume_handlers:
            try:
                h.handler(event)
            except Exception as e:
                logger.error(f"Error handling event {event} for entity {h.entity}: {e}")

    def _handle_simulation_shutdown(self, event: Event) -> None:
        """
        Handles simulation shutdown events.
        :param event: A simulation shutdown event.
        """
        assert event.event_name == ScarabEventType.SIMULATION_SHUTDOWN

        for h in self._simulation_shutdown_handlers:
            try:
                h.handler(event)
            except Exception as e:
                logger.error(f"Error handling event {event} for entity {h.entity}: {e}")

    def _handle_time_updated(self, event: Event) -> None:
        """
        Handles time updated events.
        :param event: A time updated event.
        """
        assert event.event_name == ScarabEventType.TIME_UPDATED

        for h in self._time_updated_handlers:
            try:
                h.handler(event)
            except Exception as e:
                logger.error(f"Error handling event {event} for entity {h.entity}: {e}")

    def _handle_named_event(self, event: Event) -> None:
        """
        Handles generic named events
        :param event: A general, named event.
        """
        # event handlers are stored by event name of event to be handled.
        event_handlers = self._named_event_handlers.get(event.event_name, [])
        for h in event_handlers:
            try:
                h.handler(event)
            except Exception as e:
                logger.error(f"Error handling event {event} for entity {h.entity}: {e}")
