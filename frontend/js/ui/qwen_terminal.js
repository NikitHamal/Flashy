// Qwen Free Web Terminal using Xterm.js

class QwenTerminal {
    constructor() {
        this.container = document.getElementById('qwen-terminal-container');
        this.output = document.getElementById('qwen-terminal-output');
        this.toggleBtn = document.getElementById('btn-toggle-qwen-term');
        this.closeBtn = document.getElementById('btn-close-qwen-term');
        
        this.term = null;
        this.fitAddon = null;
        this.socket = null;
        this.isOpen = false;

        this.initEventListeners();
    }

    initEventListeners() {
        if (this.toggleBtn) {
            this.toggleBtn.addEventListener('click', () => this.toggle());
        }
        if (this.closeBtn) {
            this.closeBtn.addEventListener('click', () => this.hide());
        }

        // Handle window resize
        window.addEventListener('resize', () => {
            if (this.isOpen && this.fitAddon) {
                this.fitAddon.fit();
                this.sendResize();
            }
        });
    }

    toggle() {
        if (this.isOpen) {
            this.hide();
        } else {
            this.show();
        }
    }

    show() {
        if (!this.container) return;
        this.container.classList.remove('hidden');
        this.isOpen = true;
        
        if (!this.term) {
            this.initTerminal();
        } else {
            // Need to wait for CSS transitions before fitting
            setTimeout(() => {
                this.fitAddon.fit();
            }, 100);
        }
    }

    hide() {
        if (!this.container) return;
        this.container.classList.add('hidden');
        this.isOpen = false;
    }

    initTerminal() {
        // Initialize xterm.js
        this.term = new Terminal({
            cursorBlink: true,
            theme: {
                background: '#0d1117',
                foreground: '#c9d1d9',
                cursor: '#58a6ff',
                selection: 'rgba(56, 139, 253, 0.4)',
                black: '#484f58',
                red: '#ff7b72',
                green: '#3fb950',
                yellow: '#d29922',
                blue: '#58a6ff',
                magenta: '#bc8cff',
                cyan: '#39c5cf',
                white: '#b1bac4',
                brightBlack: '#6e7681',
                brightRed: '#ffa198',
                brightGreen: '#56d364',
                brightYellow: '#e3b341',
                brightBlue: '#79c0ff',
                brightMagenta: '#d2a8ff',
                brightCyan: '#56d4dd',
                brightWhite: '#f0f6fc'
            },
            fontFamily: '"JetBrains Mono", "Cascadia Code", "Fira Code", monospace',
            fontSize: 14,
            lineHeight: 1.2
        });

        this.fitAddon = new FitAddon.FitAddon();
        this.term.loadAddon(this.fitAddon);
        
        this.term.open(this.output);
        this.fitAddon.fit();

        this.connectWebSocket();

        // Handle input
        this.term.onData((data) => {
            if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                this.socket.send(data);
            }
        });
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/terminal`;
        
        this.term.write('\r\n\x1b[1;36m[Flashy]\x1b[0m Connecting to Qwen Web Terminal...\r\n');
        
        this.socket = new WebSocket(wsUrl);
        
        this.socket.onopen = () => {
            this.term.write('\x1b[1;32m[Flashy]\x1b[0m Connected! Launching qwen-code...\r\n\n');
            this.sendResize();
        };

        this.socket.onmessage = (event) => {
            this.term.write(event.data);
        };

        this.socket.onclose = () => {
            this.term.write('\r\n\x1b[1;31m[Flashy]\x1b[0m Connection closed. Reconnecting in 3s...\r\n');
            setTimeout(() => {
                if (this.isOpen) {
                    this.connectWebSocket();
                }
            }, 3000);
        };

        this.socket.onerror = (err) => {
            console.error('Terminal WebSocket error:', err);
        };
    }

    sendResize() {
        if (this.socket && this.socket.readyState === WebSocket.OPEN && this.term) {
            const size = {
                type: 'resize',
                cols: this.term.cols,
                rows: this.term.rows
            };
            this.socket.send(JSON.stringify(size));
        }
    }
}

// Export for app.js to initialize
window.QwenTerminal = QwenTerminal;
