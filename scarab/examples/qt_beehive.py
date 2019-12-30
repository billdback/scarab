"""
Copyright (C) 2019 William D. Back

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

This module shows how to add a more complex GUI to a simulation.
This uses the beehive classes, but has a PyQt display.
"""
import sys

from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc

import random

from scarab.examples.beehive import *
from scarab.entities import *
from scarab.loggers import StdOutLogger
from scarab.simulation import Simulation, SIMULATION_LOGGING, EVENT_LOGGING, ENTITY_LOGGING

StdOutLogger(topics=SIMULATION_LOGGING)
# StdOutLogger(topics=EVENT_LOGGING)
# StdOutLogger(topics=ENTITY_LOGGING)


class BeehiveDisplayModel(Entity):
    """Manages content for display by the application.  Used instead of the beehive display class."""

    def __init__(self):
        """
        Creates a new beehive display model.
        """
        self._beehive = None
        self._outside_temp = None
        super().__init__(name="behive_display_model")

        # mins are set to a very large number so they will be properly set the next time.
        self.min_outside_temp = 1000000
        self.max_outside_temp = 0
        self.min_hive_temp = 1000000
        self.max_hive_temp = 0
        self.min_number_bees = 1000000
        self.max_number_bees = 0
        self.min_number_bees_buzzing = 1000000
        self.max_number_bees_buzzing = 0
        self.min_number_bees_fanning = 1000000
        self.max_number_bees_fanning = 0

    @entity_created_event_handler(entity_name="beehive")
    def handle_beehive_changed(self, beehive):
        """Handles the beehive changing.
        :param beehive: The beehive that changed.
        :type beehive: Entity
        """
        self._beehive = beehive

    @entity_changed_event_handler(entity_name="beehive")
    def handle_beehive_changed(self, beehive, changed_properties):
        """Handles the beehive changing.
        :param beehive: The beehive that changed.
        :type beehive: Entity
        :param changed_properties: The properties that changed.
        :type changed_properties: list of str
        """
        assert changed_properties is not None
        self._beehive = beehive

        self.min_hive_temp = min(self.min_hive_temp, self._beehive.current_temp)
        self.max_hive_temp = max(self.max_hive_temp, self._beehive.current_temp)

        self.min_number_bees = min(self.min_number_bees, self._beehive.number_bees)
        self.max_number_bees = max(self.max_number_bees, self._beehive.number_bees)
        self.min_number_bees_fanning = min(self.min_number_bees_fanning, self._beehive.number_bees_fanning)
        self.max_number_bees_fanning = max(self.max_number_bees_fanning, self._beehive.number_bees_fanning)
        self.min_number_bees_buzzing = min(self.min_number_bees_buzzing, self._beehive.number_bees_buzzing)
        self.max_number_bees_buzzing = max(self.max_number_bees_buzzing, self._beehive.number_bees_buzzing)

    @entity_changed_event_handler(entity_name="outside_temperature")
    def handle_temp_changed(self, temp, changed_properties):
        """Handles the outside temp changing.
        :param temp: The temperature entity that changed.
        :type temp: Entity
        :param changed_properties: The properties that changed.
        :type changed_properties: list of str
        :return: None
        """
        assert changed_properties
        self._outside_temp = temp.current_temp
        self.min_outside_temp = min(self.min_outside_temp, self._outside_temp)
        self.max_outside_temp = max(self.max_outside_temp, self._outside_temp)


class MainWindow(qtw.QWidget, Entity):
    """Creates a display for the simulation.  The display manages the simulation and updates."""

    def __init__(self):
        """Creates a QT UI."""
        super().__init__(flags=qtc.Qt.WindowCloseButtonHint, name="beehive_display")

        self.beehive_display_model = None

        self.setWindowTitle("Beehive")
        self.resize(1200, 600)

        self.__create_widgets()
        self.__layout_widgets()

        self.show()

    def __create_widgets(self):
        """Create the widgets that will be used in the UI."""

        # Outside temperature options.
        self.outside_temp_min_label = qtw.QLabel("Outside minimum: ")
        self.outside_temp_min_edit = qtw.QLineEdit()
        self.outside_temp_min_edit.setValidator(qtg.QIntValidator(0, 25))
        self.outside_temp_max_label = qtw.QLabel("Outside maximum: ")
        self.outside_temp_max_edit = qtw.QLineEdit()
        self.outside_temp_max_edit.setValidator(qtg.QIntValidator(50, 100))

        # Beehive temparature options.
        self.beehive_temp_min_label = qtw.QLabel("Beehive minimum: ")
        self.beehive_temp_min_edit = qtw.QLineEdit()
        self.beehive_temp_min_edit.setValidator(qtg.QIntValidator(0, 25))
        self.beehive_temp_max_label = qtw.QLabel("Beehive maximum: ")
        self.beehive_temp_max_edit = qtw.QLineEdit()
        self.beehive_temp_max_edit.setValidator(qtg.QIntValidator(50, 100))

        # Bee options.
        self.number_bees_label = qtw.QLabel("Number bees:  ")
        self.number_bees_edit = qtw.QLineEdit()
        self.number_bees_edit.setValidator(qtg.QIntValidator(1, 20))

        # Radio button options for varying bee temps.
        self.vary_bees = qtw.QRadioButton("Vary bees")
        self.no_vary_bees = qtw.QRadioButton("Don't vary bees")

        # Buttons to start/pause/resume.  Use regular exit buttons.
        self.control_button = qtw.QPushButton("Start")

        # placeholders for charts.
        self.temp_chart = qtw.QTextEdit()
        self.bee_chart = qtw.QTextEdit()

    def __layout_widgets(self):
        """Creates the layouts and lays out widgets."""
        # Main layout is horizontal with two columns.
        main_layout = qtw.QHBoxLayout()
        self.setLayout(main_layout)

        # Define layouts for each side section.
        config_control_layout = qtw.QVBoxLayout()
        main_layout.addLayout(config_control_layout, 20)
        charts_layout = qtw.QVBoxLayout()
        main_layout.addLayout(charts_layout, 80)

        # Add the group box for settings and buttons.
        configuration_form = qtw.QGroupBox("Configuration")
        config_control_layout.addWidget(configuration_form)
        config_control_layout.addWidget(self.control_button)

        # Add configuration options.
        configuration_form_details_layout = qtw.QGridLayout()
        configuration_form.setLayout(configuration_form_details_layout)

        configuration_form_details_layout.addWidget(self.number_bees_label, 1, 1)
        configuration_form_details_layout.addWidget(self.number_bees_edit, 1, 2)

        configuration_form_details_layout.addWidget(qtw.QLabel(), 2, 1, 1, 2)

        temperature_groupbox = qtw.QGroupBox("Temperature Settings")
        configuration_form_details_layout.addWidget(temperature_groupbox, 3, 1, 1, 2)
        configuration_temp_layout = qtw.QGridLayout()
        temperature_groupbox.setLayout(configuration_temp_layout)

        configuration_temp_layout.addWidget(self.outside_temp_min_label, 1, 1)
        configuration_temp_layout.addWidget(self.outside_temp_min_edit, 1, 2)
        configuration_temp_layout.addWidget(self.outside_temp_max_label, 2, 1)
        configuration_temp_layout.addWidget(self.outside_temp_max_edit, 2, 2)

        configuration_temp_layout.addWidget(self.beehive_temp_min_label, 3, 1)
        configuration_temp_layout.addWidget(self.beehive_temp_min_edit, 3, 2)
        configuration_temp_layout.addWidget(self.beehive_temp_max_label, 4, 1)
        configuration_temp_layout.addWidget(self.beehive_temp_max_edit, 4, 2)

        # Blanks for spacing.  Probably better way to do this.
        configuration_form_details_layout.addWidget(qtw.QLabel(), 4, 1, 1, 2)

        bee_groupbox = qtw.QGroupBox("Bee Behavior")
        bee_groupbox.setSizePolicy(qtw.QSizePolicy.Minimum, qtw.QSizePolicy.Minimum)
        configuration_form_details_layout.addWidget(bee_groupbox, 5, 1, 1, 2)
        vbox = qtw.QVBoxLayout()
        bee_groupbox.setLayout(vbox)

        vbox.addWidget(self.vary_bees)
        vbox.addWidget(self.no_vary_bees)

        # Add the charts to the window.
        # TODO converts to charts.  For now, use placeholders.

        temp_chart_form = qtw.QGroupBox("Temperatures")
        charts_layout.addWidget(temp_chart_form)
        temp_chart_form_layout = qtw.QVBoxLayout()
        temp_chart_form.setLayout(temp_chart_form_layout)
        temp_chart_form_layout.addWidget(self.temp_chart)

        bee_chart_form = qtw.QGroupBox("Bee Activity")
        charts_layout.addWidget(bee_chart_form)
        bee_chart_form_layout = qtw.QVBoxLayout()
        bee_chart_form.setLayout(bee_chart_form_layout)
        bee_chart_form_layout.addWidget(self.bee_chart)

    @entity_created_event_handler(entity_name="beehive_display_model")
    def handle_beehive_display_model_created(self, display_model):
        """
        Handles the display model being created.  Assumes there is only one.
        :param display_model: The display model.
        :type display_model: BeehiveDisplayModel
        """
        self.beehive_display_model = display_model

    @entity_destroyed_event_handler(entity_name="beehive_display_model")
    def handle_beehive_display_model_created(self, display_model):
        """
        Handles the display model being created.  Assumes there is only one.
        :param display_model: The display model.
        :type display_model: BeehiveDisplayModel
        """
        self.beehive_display_model = None

    @entity_changed_event_handler(entity_name="beehive_display_model")
    def handle_beehive_display_model_created(self, display_model, changed_properties):
        """
        Handles the display model being created.  Assumes there is only one.
        :param display_model: The display model.
        :type display_model: BeehiveDisplayModel
        :param changed_properties: The properties that changed.
        :type changed_properties: list of str
        """
        self.beehive_display_model = changed_properties

    @time_update_event_handler
    def handle_time_update(self, prev_time, new_time):
        """
        Handles time updates and updates the GUI.
        :param prev_time: The previous time in the simulation.
        :type prev_time: int
        :param new_time: The new time in the simulation.
        :type new_time: int
        """
        pass


if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)
    mw = MainWindow()
    sys.exit(app.exec())
