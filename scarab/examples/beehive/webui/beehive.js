/** Copyright (c) 2024 William D Back
 *
 * This file is part of Scarab licensed under the MIT License.
 * For full license text, see the LICENSE file in the project root.

 This is the main controller for the beehive simulation.  It updates based on messages from the sim and allows the user
 to send back control messages.
 */

import {WSEventHandler} from "./ws_event_handler.js";

const load_app = () => {
    console.log("Beehive UI started.");
    updateView();
};

/** Text boxes for updating. */
const simtimeTxt = document.getElementById("simtime-txt");
const totalBeesTxt = document.getElementById("total-bees-txt");
const beesFlappingTxt = document.getElementById("bees-flapping-txt");
const beesBuzzingTxt = document.getElementById("bees-buzzing-txt");
const outsideTempTxt = document.getElementById("outside-temp-txt");
const hiveTempTxt = document.getElementById("hive-temp-txt");

/** Buttons */
const startResumeButton = document.getElementById("start-resume-sim-button");
const pauseButton = document.getElementById("pause-sim-button");
const shutdownButton = document.getElementById("shutdown-sim-button");

/*

  Expected flow.  Bee creation/changes are received and then put into the end of the arrays for stats.
  When a time updated event is received, the stats and charts are all updated and then a new entry is received.
*/

class BeeHiveStats {
    constructor() {
        this.bees = {};
        this.bees_flapping_history = [];
        this.bees_buzzing_history = [];

        this.outside_temp = 0;
        this.outside_temp_history = [];

        this.hive_temp = 0;
        this.hive_temp_history = [];

        this.times = [];
    }

    addOrChangeBee(bee) {
        console.log('adding bee', bee);
        // Will add new bees or just update existing ones.
        this.bees[bee.scarab_id] = bee;
    }

    removeBee(bee) {
        delete this.bees[bee.scarab_id];
    }

    get number_bees() {
        return Object.keys(this.bees).length;
    }

    setOutdoorTemp(temp) {
        this.outside_temp = temp;
    }

    setHiveTemp(temp) {
        this.hive_temp = temp;
    }

    // Change the time and set the stats for this time.
    timeChange(time) {
        console.log(`time update at ${time}.  bees == `, this.bees)
        this.times.push(time);
        this.bees_buzzing_history.push(Object.values(this.bees).filter((bee) => bee.isBuzzing).length);
        this.bees_flapping_history.push(Object.values(this.bees).filter((bee) => bee.isFlapping).length);

        this.outside_temp_history.push(this.outside_temp);
        this.hive_temp_history.push(this.hive_temp);
    }
}

const stats = new BeeHiveStats();

// called when the time update is received.  Stats are handled as they come in.
const updateView = () => {
    showStats();
    updateCharts();
};

const showStats = () => {
    simtimeTxt.value = stats.times[stats.times.length - 1];

    totalBeesTxt.value = stats.number_bees;

    beesFlappingTxt.value = stats.bees_flapping_history[stats.bees_flapping_history.length - 1];

    beesBuzzingTxt.value = stats.bees_buzzing_history[stats.bees_buzzing_history.length - 1];

    outsideTempTxt.value = stats.outside_temp;

    hiveTempTxt.value = stats.hive_temp;
}

/* Chart controls ********************************************************************/

const updateCharts = () => {
    updateTempLineChart();
    updateBeeLineChart();
};

const tempCtx = document.getElementById("temp-line-chart").getContext("2d");
const tempLineChart = new Chart(tempCtx, {
    type: "line", data: {
        labels: stats.times, datasets: [{
            label: "Outside Temp", data: [], // stats.outside_temp_history,
            yAxisID: "y", // Reference the first y-axis
            borderColor: "rgb(255, 165, 0)", backgroundColor: "rgba(255, 165, 0, 0.75)", fill: false,
        }, {
            label: "Hive Temp", data: [], // stats.hive_temp_history,
            yAxisID: "y", // Reference the first y-axis
            borderColor: "rgb(255, 200, 102)", backgroundColor: "rgba(255, 200, 102, 0.75)", fill: false,
        },],
    }, options: {
        scales: {
            y: {
                type: "linear", position: "left", // Temperature on the left
                title: {
                    display: true, text: "Temp",
                }, ticks: {
                    beginAtZero: true,
                },
            }, x: {
                title: {
                    display: true, text: "Time",
                },
            },
        },
    },
});
const updateTempLineChart = () => {
    tempLineChart.data.datasets[0].data = stats.outside_temp_history;
    tempLineChart.data.datasets[1].data = stats.hive_temp_history;
    tempLineChart.update();
};

const beeCtx = document.getElementById("bee-line-chart").getContext("2d");
const beeLineChart = new Chart(beeCtx, {
    type: "line", data: {
        labels: stats.times, datasets: [{
            label: "Bees Flapping", data: [], // stats.bees_flapping_history,
            yAxisID: "y", borderColor: "rgb(0, 0, 255)", backgroundColor: "rgba(0, 0, 255, 0.75)", fill: false,
        }, {
            label: "Bees Buzzing", data: [], // stats.bees_buzzing_history,
            yAxisID: "y", borderColor: "rgb(173, 216, 230)", backgroundColor: "rgba(173, 216, 230, 0.75)", fill: false,
        },],
    }, options: {
        scales: {
            y: {
                type: "linear", position: "left", title: {
                    display: true, text: "Bees",
                }, ticks: {
                    beginAtZero: true,
                }, grid: {
                    drawOnChartArea: false, // Avoid grid lines overlapping
                },
            }, x: {
                title: {
                    display: true, text: "Time",
                },
            },
        },
    },
});

const updateBeeLineChart = () => {
    beeLineChart.data.datasets[0].data = stats.bees_flapping_history;
    beeLineChart.data.datasets[1].data = stats.bees_buzzing_history;

    beeLineChart.update();
};

/* Websocket stuff. *******************************************************/

// default for sim is 1234.  Would have to change if different.
const ws = new WSEventHandler("ws://localhost:1234", 5, "status");

ws.registerEventHandler("scarab.entity.created",
    (event) => event.entity.scarab_name === 'bee',
    (event) => stats.addOrChangeBee(event.entity));

ws.registerEventHandler("scarab.entity.created",
    (event) => event.entity.scarab_name === 'hive',
    (event) => stats.setHiveTemp(event.entity.current_temp));

ws.registerEventHandler("scarab.entity.created",
    (event) => event.entity.scarab_name === 'outside_temp',
    (event) => stats.setOutdoorTemp(event.entity.current_temp));

ws.registerEventHandler("scarab.entity.updated",
    (event) => event.entity.scarab_name === 'bee',
    (event) => stats.addOrChangeBee(event.entity));

ws.registerEventHandler("scarab.entity.updated",
    (event) => event.entity.scarab_name === 'hive',
    (event) => stats.setHiveTemp(event.entity.current_temp));

ws.registerEventHandler("scarab.entity.updated",
    (event) => event.entity.scarab_name === 'outside_temp',
    (event) => stats.setOutdoorTemp(event.entity.current_temp));

ws.registerEventHandler("scarab.entity.deleted",
    (event) => event.entity.scarab_name === 'bee',
    (event) => stats.removeBee(event.entity));

ws.registerEventHandler("scarab.entity.deleted",
    (event) => event.entity.scarab_name === 'hive',
    (_) => stats.setHiveTemp(NaN));

ws.registerEventHandler("scarab.entity.deleted",
    (event) => event.entity.scarab_name === 'outside-temperature',
    (_) => stats.setOutdoorTemp(NaN));

ws.registerEventHandler("scarab.time.updated"),
    (_) => true,
    (event) => stats.timeChange(event.time)

await ws.connect();


/* Button actions to control the sim. *************************************************/

// Note: () => notation is important to bind `this` correctly.
startResumeButton.addEventListener("click", () => ws.start());
pauseButton.addEventListener("click", () => ws.pause());
shutdownButton.addEventListener("click", () => ws.shutdown());

/* Start the app. ********************************************************************/

document.addEventListener("DOMContentLoaded", function () {
    load_app();
});
