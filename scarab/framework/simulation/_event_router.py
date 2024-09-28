"""
Copyright (c) 2024 William D Back

This file is part of Scarab licensed under the MIT License.
For full license text, see the LICENSE file in the project root.

Event router for routing events to the appropriate entity handlers.

NOTE: `getattr` is used throughout to handle dealing with abstract types that have already been checked for correctness.
"""

import asyncio
from collections import namedtuple
import inspect
import logging
from typing import Dict, List

from ._ws_server import WSEventServer
from ..types import EventHandler
from ..events import Event, ScarabEventType
from ..event_loggers import BaseLogger
from ..entity import scarab_properties

logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

EntityAndHandler = namedtuple('EntityAndHandler', ['entity', 'handler'])


class EventRouter:
    """
    The event router allows entities to be registered with the event router.  The router will introspect the entities
    to find their handlers and then add them.  The router can then accept messages and route them to the correct
    entities.  Finally, entities can be removed.
    """

    def __init__(self, event_logger: BaseLogger = None, ws_server: WSEventServer = None):
        """
        Create a new EventRouter that will have the handlers for the entity.

        The router contains known lists for the standard event types, such as EntityCreatedEvent, EntityUpdatedEvent,
        etc.  Then there are event routers with the name of the event, to account for general events.

        Each event type varies in how it stores the handlers.  For ones that are specific to entities, such as
        EntityCreatedEvent, the router stores in a dictionary based on the entity name (str).  Then the list contains
        the entity and handler to call.  This allows the router to invoke the method on the instance.  It also makes it
        possible to easily delete the entity when it's destroyed.
        :param event_logger: Logger for logging events.  If None, then don't log.
        :param ws_server: The websocket server to send events to.  If not provided, it won't be used.
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

        # Logger to use.
        self._event_logger = event_logger
        # Websocket server to send all events to.
        self._ws_server = ws_server

    def log_event(self, sent_to: str, event: Event):
        """
        Logs the event to the logger if one was set.
        :param sent_to: The entity or target of the event.
        :param event: The event.
        """
        if self._event_logger:
            self._event_logger.log_event(sent_to=sent_to, event=event)

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

        logger.debug(f"Registering entity: {entity.scarab_name}")

        for attr_name in dir(entity):
            attr = getattr(entity, attr_name)
            if callable(attr) and hasattr(attr, "scarab_handler") and attr.scarab_handler:
                event_type = getattr(attr, "event_type")

                logger.info(f"\tAdding handler for class {entity.scarab_name}:  {event_type}")

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
                    if event_type == ScarabEventType.ENTITY_CREATED:
                        self._register_entity_created_handler(entity_name_to_handle=getattr(attr, 'entity_name'),
                                                              entity=entity,
                                                              handler=attr)
                    elif event_type == ScarabEventType.ENTITY_CHANGED:
                        self._register_entity_changed_handler(entity_name_to_handle=getattr(attr, 'entity_name'),
                                                              entity=entity,
                                                              handler=attr)
                    elif event_type == ScarabEventType.ENTITY_DESTROYED:
                        self._register_entity_destroyed_handler(entity_name_to_handle=getattr(attr, 'entity_name'),
                                                                entity=entity,
                                                                handler=attr)
                    elif event_type == ScarabEventType.SIMULATION_START:
                        self._register_simulation_start_handler(entity=entity, handler=attr)
                    elif event_type == ScarabEventType.SIMULATION_PAUSE:
                        self._register_simulation_pause_handler(entity=entity, handler=attr)
                    elif event_type == ScarabEventType.SIMULATION_RESUME:
                        self._register_simulation_resume_handler(entity=entity, handler=attr)
                    elif event_type == ScarabEventType.SIMULATION_SHUTDOWN:
                        self._register_simulation_shutdown_handler(entity=entity, handler=attr)
                    elif event_type == ScarabEventType.TIME_UPDATED:
                        self._register_time_updated_handler(entity=entity, handler=attr)
                    elif event_type == ScarabEventType.NAMED_EVENT:
                        self._register_named_event_handler(event_name_to_handle=getattr(attr, 'event_name'),
                                                           entity=entity,
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
        scarab_id = getattr(entity, 'scarab_id', None)
        self._entity_created_handlers = {key: [item for item in value if item.entity.scarab_id != scarab_id] for
                                         key, value in self._entity_created_handlers.items()}
        self._entity_changed_handlers = {key: [item for item in value if item.entity.scarab_id != scarab_id]
                                         for
                                         key, value in self._entity_changed_handlers.items()}
        self._entity_destroyed_handlers = {
            key: [item for item in value if item.entity.scarab_id != scarab_id]
            for
            key, value in self._entity_destroyed_handlers.items()}

        # Simulation state change handlers.
        self._simulation_start_handlers = [entry for entry in self._simulation_start_handlers if
                                           entry.entity.scarab_id != scarab_id]
        self._simulation_pause_handlers = [entry for entry in self._simulation_pause_handlers if
                                           entry.entity.scarab_id != scarab_id]
        self._simulation_resume_handlers = [entry for entry in self._simulation_resume_handlers if
                                            entry.entity.scarab_id != scarab_id]
        self._simulation_shutdown_handlers = [entry for entry in self._simulation_shutdown_handlers if
                                              entry.entity.scarab_id != scarab_id]

        # Time updated events.
        self._time_updated_handlers = [entry for entry in self._time_updated_handlers if
                                       entry.entity.scarab_id != scarab_id]

        # Generic (named) events.
        self._named_event_handlers = {key: [item for item in value if item.entity.scarab_id != scarab_id] for
                                      key, value in self._named_event_handlers.items()}

    def sync_route(self, event: Event) -> None:
        """
        Routes the event synchronously.  This is provided because the normal route method is async.  Mostly this is
        to enable easier testing and should not be used for other purposes.  The simulation will call the async version.
        :param event: The event to route.
        """
        asyncio.run(self.route(event=event))

    async def route(self, event: Event) -> None:
        """
        Routes the events to all event handlers.
        :param event: The event to route.
        WARNING | FUTURE: There may be scenarios where a method and an attribute have the same names and handlers
        will fail to be registered.
        """
        logger.debug(f"Routing event {event.to_json()}")

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

        if self._ws_server:
            self.log_event(sent_to='websocket', event=event)
            await self._ws_server.send_event(event)  # this is a coroutine, so wait to finish.

    @staticmethod
    def _get_sent_to_from_handler(h: EntityAndHandler) -> str:
        """
        Gets a formatted name for the entity to log from the handler.
        """
        scarab_name = h.entity.scarab_name
        scarab_id = h.entity.scarab_id

        return f'{scarab_name} ({scarab_id})'

    def _handle_entity_created(self, event: Event) -> None:
        """
        Handles entity created events.
        :param event: An entity created event.
        """
        assert event.event_name == ScarabEventType.ENTITY_CREATED

        # event handlers are stored by entity name of entity to be handled.
        entity = getattr(event, 'entity', None)
        event_handlers = self._entity_created_handlers.get(entity.scarab_name, [])
        for h in event_handlers:
            try:
                self.log_event(sent_to=self._get_sent_to_from_handler(h), event=event)
                h.handler(event)
            except Exception as e:
                self._log_event_handling_error(event=event, entity=h.entity, ex=e)

    def _handle_entity_updated(self, event: Event) -> None:
        """
        Handles entity updated events.
        :param event: An entity updated event.
        """
        assert event.event_name == ScarabEventType.ENTITY_CHANGED

        # event handlers are stored by entity name of entity to be handled.
        entity = getattr(event, 'entity', None)
        event_handlers = self._entity_changed_handlers.get(entity.scarab_name, [])
        for h in event_handlers:
            try:
                self.log_event(sent_to=self._get_sent_to_from_handler(h), event=event)
                h.handler(event)
            except Exception as e:
                self._log_event_handling_error(event=event, entity=h.entity, ex=e)

    def _handle_entity_destroyed(self, event: Event) -> None:
        """
        Handles entity destroyed events.
        :param event: An entity destroyed event.
        """
        assert event.event_name == ScarabEventType.ENTITY_DESTROYED

        # event handlers are stored by entity name of entity to be handled.
        entity = getattr(event, 'entity', None)
        event_handlers = self._entity_destroyed_handlers.get(entity.scarab_name, [])
        for h in event_handlers:
            try:
                self.log_event(sent_to=self._get_sent_to_from_handler(h), event=event)
                h.handler(event)
            except Exception as e:
                self._log_event_handling_error(event=event, entity=h.entity, ex=e)

    def _handle_simulation_start(self, event: Event) -> None:
        """
        Handles simulation start events.
        :param event: A simulation start event.
        """
        assert event.event_name == ScarabEventType.SIMULATION_START

        for h in self._simulation_start_handlers:
            try:
                self.log_event(sent_to=self._get_sent_to_from_handler(h), event=event)
                h.handler(event)
            except Exception as e:
                self._log_event_handling_error(event=event, entity=h.entity, ex=e)

    def _handle_simulation_pause(self, event: Event) -> None:
        """
        Handles simulation pause events.
        :param event: A simulation pause event.
        """
        assert event.event_name == ScarabEventType.SIMULATION_PAUSE

        for h in self._simulation_pause_handlers:
            try:
                self.log_event(sent_to=self._get_sent_to_from_handler(h), event=event)
                h.handler(event)
            except Exception as e:
                self._log_event_handling_error(event=event, entity=h.entity, ex=e)

    def _handle_simulation_resume(self, event: Event) -> None:
        """
        Handles simulation resume events.
        :param event: A simulation resume event.
        """
        assert event.event_name == ScarabEventType.SIMULATION_RESUME

        for h in self._simulation_resume_handlers:
            try:
                self.log_event(sent_to=self._get_sent_to_from_handler(h), event=event)
                h.handler(event)
            except Exception as e:
                self._log_event_handling_error(event=event, entity=h.entity, ex=e)

    def _handle_simulation_shutdown(self, event: Event) -> None:
        """
        Handles simulation shutdown events.
        :param event: A simulation shutdown event.
        """
        assert event.event_name == ScarabEventType.SIMULATION_SHUTDOWN

        for h in self._simulation_shutdown_handlers:
            try:
                self.log_event(sent_to=self._get_sent_to_from_handler(h), event=event)
                h.handler(event)
            except Exception as e:
                self._log_event_handling_error(event=event, entity=h.entity, ex=e)

    def _handle_time_updated(self, event: Event) -> None:
        """
        Handles time updated events.
        :param event: A time updated event.
        """
        assert event.event_name == ScarabEventType.TIME_UPDATED

        for h in self._time_updated_handlers:
            try:
                self.log_event(sent_to=self._get_sent_to_from_handler(h), event=event)
                h.handler(event)
            except Exception as e:
                self._log_event_handling_error(event=event, entity=h.entity, ex=e)

    def _handle_named_event(self, event: Event) -> None:
        """
        Handles generic named events
        :param event: A general, named event.
        """
        # event handlers are stored by event name of event to be handled.
        event_handlers = self._named_event_handlers.get(event.event_name, [])
        for h in event_handlers:
            try:
                self.log_event(sent_to=self._get_sent_to_from_handler(h), event=event)
                h.handler(event)
            except Exception as e:
                self._log_event_handling_error(event=event, entity=h.entity, ex=e)

    @staticmethod
    def _log_event_handling_error(event: Event, entity, ex: Exception) -> None:
        """
        Logs a common error for errors handling events.
        :param event: The event being handled.
        :param entity: The entity that the event is to be sent to.
        :param ex: The exception that was caught.
        """
        entity_props = scarab_properties(entity)
        logger.error(f"Error handling {event.event_name} event {event} for entity {entity_props}: {ex}")
