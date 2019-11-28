# scarab

Scarab is an entity-based, time stepped, discrete event simulation network written in Python.  That means that a 
simulation is made up of individual entities that respond to discrete events that in turn can generate additional 
discrete events.  And these events and updates are based on incremental updates to time.

For example, imagine a traffic flow simulation.  It would consist of entities, such as cars and traffic lights, that
would change state based on events, such as time updates and changes in state of other entities.  A traffic light 
turns green, so the car starts to move.  The car moves a distance for each time increment based on velocity, 
acceleration, etc.

## Installation

Scarab requires Python 3.6 or later to run.  Additional dependencies can be found in the setup.py file.

You can either download or install directly from GitHub using the command:  
`pip install --upgrade git+https://github.com/billdback/scarab`

Note that this requires git and pip to be installed in your environment.

## Scarab concepts

### Simulation

A simulation is a container for entities.  It manages the lifecycle of entities as well as the routing of events
and messages between entities.  

### Events

Events are simply a message with properties that occur at a given time. 

### Entities

Entities are individual models that contain state and respond to events in the simulation.  Entities
receive events by registering handlers for events.  When an event is sent in the simulation, the simulation
looks for all of the handlers for that given event type and calls the appropriate handler.  

Note that all handlers (and entities) are identified by strings and not class names.  This design is to allow
simulations to be composed of a variety of classes that are defined on how entities and events appear to other entities.
That is, entities and events are known by their properties.  For example, a car entity may represent mulitple types of
cars, but to other entities they are defined by make, model, number of wheels, etc.

The following are the handler decorators and desciptions of the handlers.  Each is given as an example method signature
to show the expected parameters.  Note that the names of the handlers parameters aren't rigid, though consistency 
aids in reading and reusing code.

`@entity_created_event_handler(entity_nane="some-entity")<br/>
handle_some_entity_created(self, entity):
`

Handles the notification that an entity was created.  The entity is not the original class, but rather a representation
of the entity's public properties.  

`@entity_destroyed_event_handler(entity_nane="some-entity")<br/>
handle_some_entity_destroyed(self, entity):
`
Handles the notification that an entity was destroyed (removed from the simulation).  The entity is not the original 
object, but rather a representation of the entity's public properties.  

`@entity_changed_event_handler(entity_nane="some-entity")<br/>
handle_some_entity_changed(self, entity, changed_properties):
`
Handles the notification that an entity's properties changed.  The entity is not the original object, but rather a 
representation of the entity's public properties.  The changed_properties is a list of the properties that changed.

`@time_update_event_handler()<br/>
handle_time_update(self, new_time, previous_time):
`
Handles notification of time changes in the simulation.  The new time is the new time in the simulation.  The 
previous_time is the time of the last update.

`@simulation_shutdown_event_handler()<br/>
handle_simulation_shutdown(self):
`
Handles the notification that the simulation is shutting down.

`@event_handler(event_name="some-event")<br/>
handle_event(self, event):
`
Defines a handler for a given event name.  This handler is the default for all events and is used when a more 
specific handler isn't available.  Note that it is possible to write complete simulations that do not use this handler
since the specific handlers are sufficient.

## Examples

### Beehive

`python -m scarab.examples.beehive --help`

The beehive example consists of a beehive with bees.  The goal of the bees is to maintain a temperature of the hive
within acceptable bounds by buzzing (heating the hive) and fanning (cooling the hive).  As the outside temperature
changes, it causes changes to the hive temperature.  The bees respond accordingly.  A key aspect of this simulation is
to show how variability in reponses (i.e. bees buzzing and fanning at different temperatures) can keep the temperature
more stable than if all of the bees have the same tolerance.  

## Releases

Releases are planned around specific themes (sets of functionality).  In addition to the high level theme, new and
improved examples are also planned.

### Version 1.0 (Complete)

Theme: Minimum Viable Product (MVP)

Version 1.0 provides the ability to make a stand-alone simulation with entities and events.  It includes an example
simulation called beehive (see scarab.examples) that demonstrates the functionality.

Main features:
* Simulation container to hold and manage entities
* Entities with handlers and state management
* Event interest and routing

### Version 2.0 (Planned)

Theme: Performance and ease of development

The focus of version 2.0 will to increase performance, robustness, ease of creation and testing, making it easy to 
create and test simulations.  Specific, planned functionality include:

* Performance review and improvements
* Generator to simplify generating simulations
* Improved testing framework to simplify simulation testing

### Version 3.0 (Future)

Theme:  Simulation completeness

The focus of version 3.0 is to add any remaining features to enable complete simulation development, including 
verification and validation and testing.

### Version 4.0 (Future)

Theme: Distributed simulations

Version 4.0 will be focused on distributed simulations.
