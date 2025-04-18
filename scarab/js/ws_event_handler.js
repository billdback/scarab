/** Copyright (c) 2024 William D Back
 *
 * This file is part of Scarab licensed under the MIT License.
 * For full license text, see the LICENSE file in the project root.
 *
 * Contains the WS event handler class to connect to websockets, send events, and handle events.
 *
 */

export class WSEventHandler {
    /**
     * Creates an instance of WSEventHandler.
     *
     * @param {string} url - The WebSocket URL to connect to, including port.
     * @param {number} maxTries - Maximum number of connection attempts.
     * @param {string} statusDivID - The ID of the div to display connection status.
     */
    constructor(url, maxTries, statusDivID) {
        /** @public {string} */
        this.url = url;

        /** @private {number} */
        this.maxTries = maxTries;

        /** @private {string} */
        this.statusDivID = statusDivID;

        /** @private {WebSocket|null} */
        this.socket = null;

        /** @private {number} */
        this.connectionAttempts = 0;

        /** @private {Object<string, Array>} */
        this.eventHandlers = {};
    }

    /**
     * Connects to the WebSocket server.
     */
    async connect() {
        while (this.connectionAttempts < this.maxTries) {
            try {
                this.connectionAttempts++;
                this.socket = new WebSocket(this.url);

                this.socket.onopen = () => {
                    this.updateStatus("Connected to WebSocket");
                    console.log("WebSocket connection established.");
                    this.connectionAttempts = 0;
                };

                this.socket.onmessage = (messageEvent) => this.handleMessage(messageEvent);

                this.socket.onclose = () => {
                    this.updateStatus("WebSocket connection closed.");
                    console.warn("WebSocket connection closed.");
                };

                this.socket.onerror = (error) => {
                    this.updateStatus("WebSocket error.");
                    console.error("WebSocket encountered an error:", error);
                };

                return; // Exit retry loop on successful connection.
            } catch (error) {
                console.error(`Connection attempt ${this.connectionAttempts} failed. Retrying in 5 seconds...`);
                await new Promise(resolve => setTimeout(resolve, 5000));
            }
        }

        console.error("Max connection attempts reached. Could not connect to WebSocket.");
        this.updateStatus("Failed to connect after maximum attempts.");
    }

    /**
     * Sends a message to the WebSocket server.
     *
     * @param {string|Object} message - The message to send. If an object is passed, it is stringified.
     */
    sendMessage(message) {
        if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
            console.error("Cannot send message: WebSocket is not open.");
            return;
        }

        const messageString = typeof message === "string" ? message : JSON.stringify(message);
        this.socket.send(messageString);
        console.log("Message sent:", messageString);
    }

    /**
     * Sends a 'start' message to the WebSocket server.
     */
    start() {
        this.sendMessage({ action: "start" });
    }

    /**
     * Sends a 'pause' message to the WebSocket server.
     */
    pause() {
        this.sendMessage({ action: "pause" });
    }

    /**
     * Sends a 'shutdown' message to the WebSocket server.
     */
    shutdown() {
        this.sendMessage({ action: "shutdown" });
    }

    /**
     * Registers an event handler for a specific event.
     *
     * @param {string} eventName - The name of the event to handle.
     * @param {Function} criteria - A boolean function to filter events.
     * @param {Function} callback - A function to execute when the event matches.
     */
    registerEventHandler(eventName, criteria, callback) {
        if (!this.eventHandlers[eventName]) {
            this.eventHandlers[eventName] = [];
        }

        this.eventHandlers[eventName].push({ criteria, callback });
    }

    /**
     * Handles incoming messages from the WebSocket server.
     *
     * @param {MessageEvent} messageEvent - The WebSocket message event.
     */
    handleMessage(messageEvent) {
        try {
            const data = JSON.parse(messageEvent.data);
            const eventName = data.event_name;

            if (!eventName || !this.eventHandlers[eventName]) {
                console.warn(`Unhandled event: ${eventName}`);
                return;
            }

            this.eventHandlers[eventName].forEach(handler => {
                if (handler.criteria(data)) {
                    handler.callback(data);
                }
            });
        } catch (error) {
            console.error("Failed to handle incoming message:", error);
        }
    }

    /**
     * Updates the status div with a message.
     *
     * @param {string} message - The message to display in the status div.
     */
    updateStatus(message) {
        const statusDiv = document.getElementById(this.statusDivID);
        if (statusDiv) {
            statusDiv.textContent = message;
        }
    }
}