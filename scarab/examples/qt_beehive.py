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
from scarab.simulation import Simulation, ViewInterface, SIMULATION_LOGGING, EVENT_LOGGING, ENTITY_LOGGING

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
    def handle_beehive_changed(self, beehive) -> None:
        """
        Handles the beehive changing.
        :param RemoteEntity beehive: The beehive that changed.
        """
        self._beehive = beehive

    @entity_changed_event_handler(entity_name="beehive")
    def handle_beehive_changed(self, beehive, changed_properties) -> None:
        """
        Handles the beehive changing.
        :param RemoteEntity beehive: The beehive that changed.
        :param list of str changed_properties: The properties that changed.
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
    def handle_temp_changed(self, temp, changed_properties) -> None:
        """
        Handles the outside temp changing.
        :param RemoteEntity temp: The temperature entity that changed.
        :param list of str changed_properties: The properties that changed.
        :return: None
        """
        assert changed_properties
        self._outside_temp = temp.current_temp
        self.min_outside_temp = min(self.min_outside_temp, self._outside_temp)
        self.max_outside_temp = max(self.max_outside_temp, self._outside_temp)


class MainWindow(qtw.QWidget):
    """Creates a display for the simulation.  The display manages the simulation and updates."""

    def __init__(self):
        """Creates a QT UI."""
        super().__init__(flags=qtc.Qt.WindowCloseButtonHint)

        self.simulation = Simulation(name="QtBeehive")

        self.setWindowTitle("Beehive")
        self.resize(1200, 600)

        self._create_widgets()
        self._layout_widgets()
        self._setup_actions()

        self.show()

    def _create_simulation(self) -> None:
        """Creates the simulation based on the settings."""

        # Get the settings and make sure they are valid.
        try:
            number_bees = int(self.number_bees_edit.text())
            vary_bees = self.vary_bees.isChecked()

            outside_min_temp = float(self.outside_temp_min_edit.text())
            outside_max_temp = float(self.outside_temp_max_edit.text())

            buzzing_impact = float(self.beehive_buzzing_impact_edit.text())
            fanning_impact = float(self.beehive_fanning_impact_edit.text())

            with self.simulation as simulation:
                self.simulation.register_view(
                    view=ViewInterface(name="Beehive View", callback=self._handle_simulation_update))
                # Create the entities.
                self.simulation.add_entity(BeehiveDisplayModel())
                self.simulation.add_entity(OutsideTemperature(min_temp=outside_min_temp, max_temp=outside_max_temp))
                self.simulation.add_entity(Beehive(start_temp=outside_min_temp,
                                                   buzzing_impact=buzzing_impact, fanning_impact=fanning_impact))

        except Exception as e:
            print(f"Error creating the simulation: {e}")

    def _handle_simulation_update(self, previous_time, new_time) -> None:
        """
        Handles the simulation updating.
        :param int previous_time: The previous simulation time.
        :param int new_time: The new simulation time.
        :return: None
        """
        print("got new simulation time.")
        if new_time % 100 == 0:
            self.temp_chart.setText(f"Advancing time to {new_time}")

    def _create_widgets(self) -> None:
        """Create the widgets that will be used in the UI."""

        # Outside temperature options.
        self.outside_temp_min_label = qtw.QLabel("Outside minimum: ")
        self.outside_temp_min_edit = qtw.QLineEdit()
        self.outside_temp_min_edit.setText("20.0")
        self.outside_temp_min_edit.setValidator(qtg.QIntValidator(0, 25))
        self.outside_temp_max_label = qtw.QLabel("Outside maximum: ")
        self.outside_temp_max_edit = qtw.QLineEdit()
        self.outside_temp_max_edit.setText("90.0")
        self.outside_temp_max_edit.setValidator(qtg.QIntValidator(50, 100))

        # Beehive temparature options.
        self.beehive_buzzing_impact_label = qtw.QLabel("Buzzing impact: ")
        self.beehive_buzzing_impact_edit = qtw.QLineEdit()
        self.beehive_buzzing_impact_edit.setText("0.5")
        self.beehive_fanning_impact_label = qtw.QLabel("Fanning impact: ")
        self.beehive_fanning_impact_edit = qtw.QLineEdit()
        self.beehive_fanning_impact_edit.setText("0.5")

        # Bee options.
        self.number_bees_label = qtw.QLabel("Number bees:  ")
        self.number_bees_edit = qtw.QLineEdit()
        self.number_bees_edit.setValidator(qtg.QIntValidator(1, 20))
        self.number_bees_edit.setText("20")

        # Radio button options for varying bee temps.
        self.vary_bees = qtw.QRadioButton("Vary bees")
        self.no_vary_bees = qtw.QRadioButton("Don't vary bees")
        self.vary_bees.setChecked(True)

        # Buttons to start/pause/resume and exit.
        self.start_pause_button = qtw.QPushButton("Start")
        self.exit_button = qtw.QPushButton("Exit")

        # placeholders for charts.
        self.temp_chart = qtw.QTextEdit()
        self.bee_chart = qtw.QTextEdit()

    def _layout_widgets(self) -> None:
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
        config_control_layout.addWidget(self.start_pause_button)
        config_control_layout.addWidget(self.exit_button)

        # Add configuration options.
        configuration_form_details_layout = qtw.QGridLayout()
        configuration_form.setLayout(configuration_form_details_layout)

        bee_groupbox = qtw.QGroupBox("Bee Settings")
        configuration_form_details_layout.addWidget(bee_groupbox, 1, 1, 1, 2)
        configuration_bee_layout = qtw.QGridLayout()
        bee_groupbox.setLayout(configuration_bee_layout)

        configuration_bee_layout.addWidget(self.beehive_buzzing_impact_label, 3, 1)
        configuration_bee_layout.addWidget(self.beehive_buzzing_impact_edit, 3, 2)
        configuration_bee_layout.addWidget(self.beehive_fanning_impact_label, 4, 1)
        configuration_bee_layout.addWidget(self.beehive_fanning_impact_edit, 4, 2)

        configuration_bee_layout.addWidget(self.number_bees_label, 1, 1)
        configuration_bee_layout.addWidget(self.number_bees_edit, 1, 2)

        configuration_form_details_layout.addWidget(qtw.QLabel(), 2, 1, 1, 2)

        temperature_groupbox = qtw.QGroupBox("Temperature Settings")
        configuration_form_details_layout.addWidget(temperature_groupbox, 3, 1, 1, 2)
        configuration_temp_layout = qtw.QGridLayout()
        temperature_groupbox.setLayout(configuration_temp_layout)

        configuration_temp_layout.addWidget(self.outside_temp_min_label, 1, 1)
        configuration_temp_layout.addWidget(self.outside_temp_min_edit, 1, 2)
        configuration_temp_layout.addWidget(self.outside_temp_max_label, 2, 1)
        configuration_temp_layout.addWidget(self.outside_temp_max_edit, 2, 2)

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

    def _setup_actions(self) -> None:
        """
        Sets up the widget actions.  Only the buttons actually have actions.
        """
        self.start_pause_button.clicked.connect(self.start_pause_button_clicked)
        self.exit_button.clicked.connect(self.exit_button_clicked)

    @qtc.pyqtSlot()
    def start_pause_button_clicked(self) -> None:
        """Handles clicks to the start/pause button."""
        button_text = self.start_pause_button.text()
        if button_text == "Start":
            print("Starting the simulation.")
            self.start_pause_button.setText("Pause")
            self._create_simulation()
            self.simulation.advance()
        elif button_text == "Pause":
            print("Pausing the simulation.")
            self.start_pause_button.setText("Resume")
            self.simulation.pause()
        elif button_text == "Resume":
            print("Resuming the simulation.")
            self.start_pause_button.setText("Pause")
            self.simulation.advance()
        else:
            print("Unknown state - not doing anything.")

    @qtc.pyqtSlot()
    def exit_button_clicked(self) -> None:
        print("Exiting")
        self.simulation.shutdown()
        self.close()


if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)
    mw = MainWindow()
    sys.exit(app.exec())
