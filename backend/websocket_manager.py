"""
WebSocket Manager for Flashy
Handles real-time bidirectional communication between frontend and backend.
"""

import asyncio
import json
from typing import Dict, Set, Optional, Callable
from fastapi import WebSocket, WebSocketDisconnect
from dataclasses import dataclass, field
from enum import Enum


class MessageType(str, Enum):
    """Types of WebSocket messages."""
    # Client -> Server
    CHAT_MESSAGE = "chat_message"
    INTERRUPT = "interrupt"
    SUBSCRIBE_TERMINAL = "subscribe_terminal"
    TERMINAL_INPUT = "terminal_input"
    
    # Server -> Client
    THOUGHT = "thought"
    TEXT = "text"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    TERMINAL_OUTPUT = "terminal_output"
    TERMINAL_EXIT = "terminal_exit"
    ERROR = "error"
    STREAM_END = "stream_end"


@dataclass
class Connection:
    """Represents a WebSocket connection."""
    websocket: WebSocket
    session_id: Optional[str] = None
    workspace_id: Optional[str] = None
    subscribed_terminals: Set[str] = field(default_factory=set)


class WebSocketManager:
    """
    Manages WebSocket connections and message routing.
    
    Features:
    - Multiple concurrent connections per session
    - Terminal output broadcasting
    - Graceful disconnection handling
    """

    def __init__(self):
        # connection_id -> Connection
        self.connections: Dict[str, Connection] = {}
        # session_id -> set of connection_ids
        self.session_connections: Dict[str, Set[str]] = {}
        # terminal_id -> set of connection_ids subscribed
        self.terminal_subscribers: Dict[str, Set[str]] = {}
        # Running terminals: terminal_id -> asyncio.subprocess.Process
        self.terminals: Dict[str, asyncio.subprocess.Process] = {}
        self._connection_counter = 0

    def _generate_connection_id(self) -> str:
        self._connection_counter += 1
        return f"conn_{self._connection_counter}"

    async def connect(self, websocket: WebSocket, session_id: str = None, workspace_id: str = None) -> str:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        
        connection_id = self._generate_connection_id()
        self.connections[connection_id] = Connection(
            websocket=websocket,
            session_id=session_id,
            workspace_id=workspace_id
        )
        
        if session_id:
            if session_id not in self.session_connections:
                self.session_connections[session_id] = set()
            self.session_connections[session_id].add(connection_id)
        
        print(f"[WS] Connection {connection_id} established (session: {session_id})")
        return connection_id

    async def disconnect(self, connection_id: str):
        """Handle WebSocket disconnection."""
        if connection_id not in self.connections:
            return
        
        conn = self.connections[connection_id]
        
        # Remove from session tracking
        if conn.session_id and conn.session_id in self.session_connections:
            self.session_connections[conn.session_id].discard(connection_id)
            if not self.session_connections[conn.session_id]:
                del self.session_connections[conn.session_id]
        
        # Remove from terminal subscriptions
        for terminal_id in conn.subscribed_terminals:
            if terminal_id in self.terminal_subscribers:
                self.terminal_subscribers[terminal_id].discard(connection_id)
        
        del self.connections[connection_id]
        print(f"[WS] Connection {connection_id} closed")

    async def send_to_connection(self, connection_id: str, message_type: MessageType, data: dict):
        """Send a message to a specific connection."""
        if connection_id not in self.connections:
            return
        
        try:
            await self.connections[connection_id].websocket.send_json({
                "type": message_type.value,
                **data
            })
        except Exception as e:
            print(f"[WS] Error sending to {connection_id}: {e}")
            await self.disconnect(connection_id)

    async def send_to_session(self, session_id: str, message_type: MessageType, data: dict):
        """Broadcast a message to all connections in a session."""
        if session_id not in self.session_connections:
            return
        
        # Copy set to avoid modification during iteration
        connection_ids = list(self.session_connections.get(session_id, set()))
        for connection_id in connection_ids:
            await self.send_to_connection(connection_id, message_type, data)

    async def broadcast_terminal_output(self, terminal_id: str, output: str, is_error: bool = False):
        """Send terminal output to all subscribed connections."""
        if terminal_id not in self.terminal_subscribers:
            return
        
        connection_ids = list(self.terminal_subscribers.get(terminal_id, set()))
        for connection_id in connection_ids:
            await self.send_to_connection(
                connection_id,
                MessageType.TERMINAL_OUTPUT,
                {"terminal_id": terminal_id, "output": output, "is_error": is_error}
            )

    def subscribe_to_terminal(self, connection_id: str, terminal_id: str):
        """Subscribe a connection to terminal output."""
        if connection_id not in self.connections:
            return
        
        if terminal_id not in self.terminal_subscribers:
            self.terminal_subscribers[terminal_id] = set()
        
        self.terminal_subscribers[terminal_id].add(connection_id)
        self.connections[connection_id].subscribed_terminals.add(terminal_id)

    async def run_streaming_command(
        self, 
        command: str, 
        terminal_id: str, 
        cwd: str = None,
        on_complete: Callable = None
    ) -> int:
        """
        Run a command with real-time output streaming via WebSocket.
        Returns the exit code.
        """
        import subprocess
        import sys
        
        try:
            # Create subprocess with pipes
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                # On Windows, we need shell=True which is default for create_subprocess_shell
            )
            
            self.terminals[terminal_id] = process
            
            async def read_stream(stream, is_error=False):
                """Read from stream and broadcast output."""
                while True:
                    # Read in chunks for responsiveness
                    chunk = await stream.read(256)
                    if not chunk:
                        break
                    
                    text = chunk.decode('utf-8', errors='replace')
                    await self.broadcast_terminal_output(terminal_id, text, is_error)
            
            # Read stdout and stderr concurrently
            await asyncio.gather(
                read_stream(process.stdout, False),
                read_stream(process.stderr, True)
            )
            
            # Wait for process to complete
            exit_code = await process.wait()
            
            # Notify completion
            for conn_id in list(self.terminal_subscribers.get(terminal_id, set())):
                await self.send_to_connection(
                    conn_id,
                    MessageType.TERMINAL_EXIT,
                    {"terminal_id": terminal_id, "exit_code": exit_code}
                )
            
            # Cleanup
            if terminal_id in self.terminals:
                del self.terminals[terminal_id]
            
            if on_complete:
                on_complete(exit_code)
            
            return exit_code
            
        except Exception as e:
            error_msg = f"Error running command: {str(e)}"
            await self.broadcast_terminal_output(terminal_id, error_msg, is_error=True)
            return -1

    async def send_terminal_input(self, terminal_id: str, input_text: str):
        """Send input to a running terminal."""
        if terminal_id not in self.terminals:
            return False
        
        process = self.terminals[terminal_id]
        if process.stdin:
            process.stdin.write(input_text.encode())
            await process.stdin.drain()
            return True
        return False

    async def kill_terminal(self, terminal_id: str):
        """Kill a running terminal process."""
        if terminal_id not in self.terminals:
            return False
        
        process = self.terminals[terminal_id]
        process.terminate()
        return True


# Global instance
ws_manager = WebSocketManager()
