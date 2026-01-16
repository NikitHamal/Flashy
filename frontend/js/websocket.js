/**
 * WebSocket Client for Flashy
 * Handles real-time bidirectional communication with the backend.
 */

class FlashyWebSocket {
    constructor() {
        this.ws = null;
        this.sessionId = null;
        this.workspaceId = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.pingInterval = null;
        this.lastPong = Date.now();

        // Event handlers
        this.handlers = {
            thought: [],
            text: [],
            tool_call: [],
            tool_result: [],
            terminal_output: [],
            terminal_exit: [],
            error: [],
            stream_end: [],
            connected: [],
            disconnected: [],
            pong: []
        };

        // Pending messages queue (for when reconnecting)
        this.pendingMessages = [];
    }

    /**
     * Connect to WebSocket server
     */
    connect(sessionId, workspaceId = null) {
        if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
            // Already connected/connecting to same session
            if (this.sessionId === sessionId) {
                return Promise.resolve();
            }
            // Different session, close old connection
            this._stopPing();
            this.ws.close();
        }

        this.sessionId = sessionId;
        this.workspaceId = workspaceId;

        return new Promise((resolve, reject) => {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = window.location.host;
            let url = `${protocol}//${host}/ws/${sessionId}`;

            if (workspaceId) {
                url += `?workspace_id=${workspaceId}`;
            }

            console.log('[WS] Connecting to:', url);
            this.ws = new WebSocket(url);

            this.ws.onopen = () => {
                console.log('[WS] Connected');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.lastPong = Date.now();
                this._startPing();
                this._emit('connected', { sessionId, workspaceId });

                // Send any pending messages
                while (this.pendingMessages.length > 0) {
                    const msg = this.pendingMessages.shift();
                    this.send(msg);
                }

                resolve();
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this._handleMessage(data);
                } catch (e) {
                    console.error('[WS] Error parsing message:', e);
                }
            };

            this.ws.onerror = (error) => {
                console.error('[WS] Error:', error);
                this._stopPing();
                reject(error);
            };

            this.ws.onclose = (event) => {
                console.log('[WS] Disconnected:', event.code, event.reason);
                this.isConnected = false;
                this._stopPing();
                this._emit('disconnected', { code: event.code, reason: event.reason });

                // Attempt reconnection if not intentional close
                if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
                    this._scheduleReconnect();
                }
            };
        });
    }

    /**
     * Start sending periodic pings to keep connection alive
     */
    _startPing() {
        this._stopPing();
        this.pingInterval = setInterval(() => {
            if (this.connected) {
                this.send({ type: 'ping' });

                // If no pong for 45 seconds, reconnect
                if (Date.now() - this.lastPong > 45000) {
                    console.warn('[WS] No pong received for 45s, reconnecting...');
                    this.ws.close();
                }
            }
        }, 30000); // Ping every 30s
    }

    /**
     * Stop sending pings
     */
    _stopPing() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
    }

    /**
     * Schedule a reconnection attempt
     */
    _scheduleReconnect() {
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

        setTimeout(() => {
            if (!this.isConnected && this.sessionId) {
                this.connect(this.sessionId, this.workspaceId).catch(() => { });
            }
        }, delay);
    }

    /**
     * Handle incoming WebSocket message
     */
    _handleMessage(data) {
        const type = data.type;

        switch (type) {
            case 'pong':
                this.lastPong = Date.now();
                this._emit('pong', data);
                break;
            case 'thought':
                this._emit('thought', data.content);
                break;
            case 'text':
                this._emit('text', {
                    content: data.content,
                    images: data.images || [],
                    is_final: data.is_final || false
                });
                break;
            case 'tool_call':
                this._emit('tool_call', {
                    name: data.name,
                    args: data.args
                });
                break;
            case 'tool_result':
                this._emit('tool_result', data.content);
                break;
            case 'terminal_output':
                this._emit('terminal_output', {
                    terminal_id: data.terminal_id,
                    output: data.output,
                    is_error: data.is_error || false
                });
                break;
            case 'terminal_exit':
                this._emit('terminal_exit', {
                    terminal_id: data.terminal_id,
                    exit_code: data.exit_code
                });
                break;
            case 'error':
                this._emit('error', data.message);
                break;
            case 'stream_end':
                this._emit('stream_end', {});
                break;
            default:
                console.warn('[WS] Unknown message type:', type);
        }
    }

    /**
     * Emit event to all registered handlers
     */
    _emit(event, data) {
        if (this.handlers[event]) {
            this.handlers[event].forEach(handler => {
                try {
                    handler(data);
                } catch (e) {
                    console.error(`[WS] Error in handler for ${event}:`, e);
                }
            });
        }
    }

    /**
     * Register event handler
     */
    on(event, handler) {
        if (this.handlers[event]) {
            this.handlers[event].push(handler);
        }
        return this; // For chaining
    }

    /**
     * Remove event handler
     */
    off(event, handler) {
        if (this.handlers[event]) {
            this.handlers[event] = this.handlers[event].filter(h => h !== handler);
        }
        return this;
    }

    /**
     * Send a message to the server
     */
    send(message) {
        if (this.connected) {
            try {
                this.ws.send(JSON.stringify(message));
                return true;
            } catch (e) {
                console.error('[WS] Error sending message:', e);
                this.pendingMessages.push(message);
                return false;
            }
        } else {
            // Queue message for when we reconnect (except for pings)
            if (message.type !== 'ping') {
                this.pendingMessages.push(message);
            }
            return false;
        }
    }

    /**
     * Send a chat message
     */
    sendChatMessage(message, files = []) {
        return this.send({
            type: 'chat_message',
            message: message,
            workspace_id: this.workspaceId,
            files: files
        });
    }

    /**
     * Interrupt the current agent session
     */
    interrupt() {
        return this.send({
            type: 'interrupt'
        });
    }

    /**
     * Run a command with streaming output
     */
    runCommand(command, cwd = null, terminalId = null) {
        const id = terminalId || `term_${Date.now()}`;
        this.send({
            type: 'run_command',
            command: command,
            cwd: cwd,
            terminal_id: id
        });
        return id;
    }

    /**
     * Send input to a running terminal
     */
    sendTerminalInput(terminalId, input) {
        return this.send({
            type: 'terminal_input',
            terminal_id: terminalId,
            input: input
        });
    }

    /**
     * Kill a running terminal
     */
    killTerminal(terminalId) {
        return this.send({
            type: 'kill_terminal',
            terminal_id: terminalId
        });
    }

    /**
     * Subscribe to terminal output
     */
    subscribeToTerminal(terminalId) {
        return this.send({
            type: 'subscribe_terminal',
            terminal_id: terminalId
        });
    }

    /**
     * Close the WebSocket connection
     */
    disconnect() {
        this._stopPing();
        if (this.ws) {
            this.ws.close(1000, 'Client disconnected');
            this.ws = null;
        }
        this.isConnected = false;
        this.sessionId = null;
    }

    /**
     * Check if connected
     */
    get connected() {
        return this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN;
    }
}

// Global instance
const flashyWS = new FlashyWebSocket();
