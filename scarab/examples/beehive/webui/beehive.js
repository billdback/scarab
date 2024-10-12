/** Copyright (c) 2024 William D Back
 *
 * This file is part of Scarab licensed under the MIT License.
 * For full license text, see the LICENSE file in the project root.

 This is the main controller for the beehive simulation.  It updates based on messages from the sim and allows the user
 to send back control messages.
 */

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

// TODO - fix the events and such after getting them.
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
        this.bees_buzzing_history.push(
            Object.values(this.bees).filter((bee) => bee.isBuzzing).length
        );
        this.bees_flapping_history.push(
            Object.values(this.bees).filter((bee) => bee.isFlapping).length
        );

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

    beesFlappingTxt.value =
        stats.bees_flapping_history[stats.bees_flapping_history.length - 1];

    beesBuzzingTxt.value =
        stats.bees_buzzing_history[stats.bees_buzzing_history.length - 1];

    outsideTempTxt.value = stats.outside_temp;

    hiveTempTxt.value = stats.hive_temp;
};

/* Event handlers ********************************************************************/
const handleTimeUpdated = (event) => {
    stats.timeChange(event.sim_time);
    updateView();
}

const handleEntityCreated = (event) => {
    // Handles the creation of entities.  Only the bees are remembered.  Temps are stored.
    if (event.entity.scarab_name === 'bee') {
        stats.addOrChangeBee(event.entity);
    } else if (event.entity.scarab_name === 'hive') {
        stats.hive_temp = event.entity.current_temp;
    } else if (event.entity.scarab_name === 'outside-temperature') {
        stats.outside_temp = event.entity.current_temp;
    } else {
        console.error(`unexpected entity type ${event.entity.scarab_name}`)
    }
}

const handleEntityChanged = (event) => {
    handleEntityCreated(event);  // logic is the same.
}

const handleEntityDeleted = (event) => {

    if (event.entity.scarab_name === 'bee') {
        stats.removeBee(event.entity);
    } else if (event.entity.scarab_name === 'hive') {
        stats.hive_temp = NaN;  // will this break?
    } else if (event.entity.scarab_name === 'outside-temperature') {
        stats.outside_temp = NaN;  // will this break?
    } else {
        console.error(`unexpected entity type ${event.entity.scarab_name}`)
    }

}

/* Chart controls ********************************************************************/

const updateCharts = () => {
    updateTempLineChart();
    updateBeeLineChart();
};

const tempCtx = document.getElementById("temp-line-chart").getContext("2d");
const tempLineChart = new Chart(tempCtx, {
    type: "line",
    data: {
        labels: stats.times,
        datasets: [
            {
                label: "Outside Temp",
                data: [], // stats.outside_temp_history,
                yAxisID: "y", // Reference the first y-axis
                borderColor: "rgb(255, 165, 0)",
                backgroundColor: "rgba(255, 165, 0, 0.75)",
                fill: false,
            },
            {
                label: "Hive Temp",
                data: [], // stats.hive_temp_history,
                yAxisID: "y", // Reference the first y-axis
                borderColor: "rgb(255, 200, 102)",
                backgroundColor: "rgba(255, 200, 102, 0.75)",
                fill: false,
            },
        ],
    },
    options: {
        scales: {
            y: {
                type: "linear",
                position: "left", // Temperature on the left
                title: {
                    display: true,
                    text: "Temp",
                },
                ticks: {
                    beginAtZero: true,
                },
            },
            x: {
                title: {
                    display: true,
                    text: "Time",
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
    type: "line",
    data: {
        labels: stats.times,
        datasets: [
            {
                label: "Bees Flapping",
                data: [], // stats.bees_flapping_history,
                yAxisID: "y",
                borderColor: "rgb(0, 0, 255)",
                backgroundColor: "rgba(0, 0, 255, 0.75)",
                fill: false,
            },
            {
                label: "Bees Buzzing",
                data: [], // stats.bees_buzzing_history,
                yAxisID: "y",
                borderColor: "rgb(173, 216, 230)",
                backgroundColor: "rgba(173, 216, 230, 0.75)",
                fill: false,
            },
        ],
    },
    options: {
        scales: {
            y: {
                type: "linear",
                position: "left",
                title: {
                    display: true,
                    text: "Bees",
                },
                ticks: {
                    beginAtZero: true,
                },
                grid: {
                    drawOnChartArea: false, // Avoid grid lines overlapping
                },
            },
            x: {
                title: {
                    display: true,
                    text: "Time",
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
const ws = new WebSocket("ws://localhost:1234");

const statusDiv = document.getElementById("status");

// Connection opened
ws.onopen = () => {
    console.log("Connected to WebSocket server");
    statusDiv.textContent = "Connected to server.";
};

// Listen for messages
ws.onmessage = (event) => {
    try {
        const simEvent = JSON.parse(event.data);
        if ('event_name' in simEvent) {  // it's _probably_ a scarab event that we can handle.
            console.log('event', simEvent)
            switch (simEvent.event_name) {
                case 'scarab.time.updated':
                    handleTimeUpdated(simEvent);
                    break;
                case 'scarab.entity.created':
                    handleEntityCreated(simEvent);
                    break;
                case 'scarab.entity.changed':
                    handleEntityChanged(simEvent);
                    break;
                case 'scarab.entity.deleted':
                    handleEntityDeleted(simEvent);
                    break;
                default:
                    console.log('unhandled event', simEvent);
            }
        } else {
            console.log('... unexpected event');
        }

    } catch (e) {
        console.error("Error parsing message:", e);
    }
};

// Handle connection close
ws.onclose = () => {
    console.log("Disconnected from WebSocket server");
    statusDiv.textContent = "Disconnected from server.";
};

// Handle errors
ws.onerror = (error) => {
    console.error("WebSocket error:", error);
    statusDiv.textContent = "WebSocket error.";
};

/* Button actions. *******************************************************/

const startOrResume = () => {
    sendWSMessage('start');
};
startResumeButton.addEventListener("click", startOrResume);

const pause = () => {
    sendWSMessage('pause');
};
pauseButton.addEventListener("click", pause);

const shutdown = () => {
    sendWSMessage('shutdown')
};
shutdownButton.addEventListener("click", shutdown);

const sendWSMessage = (message) => {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(message);
        console.log("Sent message to server:", message);
    } else {
        console.warn("WebSocket is not open. Unable to send message.");
    }

}

/* Start the app. ********************************************************************/

document.addEventListener("DOMContentLoaded", function () {
    load_app();
});
