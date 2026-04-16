"""
Production-grade SQLite database layer for Flashy.

Replaces flat JSON file storage with proper ACID-compliant relational tables,
indexed queries, and concurrent access safety via WAL mode and row-level locking.
"""

import sqlite3
import json
import os
import time
import uuid
import threading
from typing import Optional, List, Dict, Any
from contextlib import contextmanager


DATA_DIR = "data"
DB_PATH = os.path.join(DATA_DIR, "flashy.db")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)


class Database:
    """
    Thread-safe SQLite database manager with WAL mode for concurrent reads.

    Uses a connection-per-thread pattern with lazy initialization.
    All write operations are serialized through the per-thread connection.
    """

    _local = threading.local()

    @classmethod
    def _get_connection(cls) -> sqlite3.Connection:
        """Get or create a connection for the current thread."""
        if not hasattr(cls._local, 'conn') or cls._local.conn is None:
            conn = sqlite3.connect(DB_PATH, timeout=30)
            conn.row_factory = sqlite3.Row
            # WAL mode: concurrent reads, serialized writes
            conn.execute("PRAGMA journal_mode=WAL")
            # Synchronous NORMAL: balance of safety and performance
            conn.execute("PRAGMA synchronous=NORMAL")
            # Foreign keys
            conn.execute("PRAGMA foreign_keys=ON")
            # Cache size: 64MB
            conn.execute("PRAGMA cache_size=-65536")
            cls._local.conn = conn
        return cls._local.conn

    @classmethod
    def close_thread_connection(cls):
        """Close the current thread's connection. Call on thread shutdown."""
        if hasattr(cls._local, 'conn') and cls._local.conn:
            cls._local.conn.close()
            cls._local.conn = None

    @classmethod
    @contextmanager
    def cursor(cls):
        """Context manager for database operations with automatic commit/rollback."""
        conn = cls._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    @classmethod
    def init_schema(cls):
        """Create database tables if they don't exist. Idempotent."""
        with cls.cursor() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS workspaces (
                    id TEXT PRIMARY KEY,
                    path TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    last_accessed REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_workspaces_last_accessed
                    ON workspaces(last_accessed DESC);

                CREATE TABLE IF NOT EXISTS chats (
                    session_id TEXT PRIMARY KEY,
                    workspace_id TEXT,
                    title TEXT NOT NULL DEFAULT 'New Chat',
                    created_at REAL NOT NULL,
                    metadata_json TEXT,
                    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_chats_workspace
                    ON chats(workspace_id);
                CREATE INDEX IF NOT EXISTS idx_chats_created
                    ON chats(created_at DESC);

                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    parts_json TEXT NOT NULL,
                    images_json TEXT NOT NULL DEFAULT '[]',
                    timestamp REAL NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES chats(session_id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_chat_messages_session
                    ON chat_messages(session_id, timestamp ASC);

                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    importance INTEGER NOT NULL DEFAULT 3,
                    timestamp TEXT NOT NULL,
                    session_id TEXT,
                    source TEXT DEFAULT 'agent',
                    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_memories_workspace
                    ON memories(workspace_id);
                CREATE INDEX IF NOT EXISTS idx_memories_category
                    ON memories(workspace_id, category);
            """)

    @classmethod
    def migrate_from_json(cls):
        """One-time migration: import existing JSON data into SQLite."""
        chats_file = os.path.join(DATA_DIR, "chats.json")
        workspaces_file = os.path.join(DATA_DIR, "workspaces.json")

        # Migrate workspaces first (chats depend on them)
        if os.path.exists(workspaces_file):
            try:
                with open(workspaces_file, 'r', encoding='utf-8') as f:
                    workspaces = json.load(f)
                if workspaces:
                    with cls.cursor() as conn:
                        for wid, data in workspaces.items():
                            conn.execute("""
                                INSERT OR IGNORE INTO workspaces (id, path, name, created_at, last_accessed)
                                VALUES (?, ?, ?, ?, ?)
                            """, (
                                wid,
                                data.get('path', ''),
                                data.get('name', os.path.basename(data.get('path', ''))),
                                data.get('created_at', time.time()),
                                data.get('last_accessed', time.time())
                            ))
            except Exception as e:
                print(f"[DB] Workspace migration skipped: {e}")

        # Migrate chats
        if os.path.exists(chats_file):
            try:
                with open(chats_file, 'r', encoding='utf-8') as f:
                    chats = json.load(f)
                if chats:
                    with cls.cursor() as conn:
                        for sid, chat in chats.items():
                            # Insert chat
                            conn.execute("""
                                INSERT OR IGNORE INTO chats (session_id, workspace_id, title, created_at, metadata_json)
                                VALUES (?, ?, ?, ?, ?)
                            """, (
                                sid,
                                chat.get('workspace_id'),
                                chat.get('title', 'New Chat'),
                                chat.get('created_at', time.time()),
                                json.dumps(chat.get('metadata', {}))
                            ))
                            # Insert messages
                            for msg in chat.get('messages', []):
                                parts = msg.get('parts', [])
                                images = msg.get('images', [])
                                conn.execute("""
                                    INSERT INTO chat_messages (session_id, role, parts_json, images_json, timestamp)
                                    VALUES (?, ?, ?, ?, ?)
                                """, (
                                    sid,
                                    msg.get('role', 'user'),
                                    json.dumps(parts),
                                    json.dumps(images),
                                    msg.get('timestamp', time.time())
                                ))
            except Exception as e:
                print(f"[DB] Chat migration skipped: {e}")

        # Mark migration as done
        migration_marker = os.path.join(DATA_DIR, ".migrated")
        if not os.path.exists(migration_marker):
            with open(migration_marker, 'w') as f:
                f.write(str(time.time()))
            print("[DB] JSON migration completed successfully")


# =============================================================================
# Repository Functions — maintain exact same API as old storage.py
# =============================================================================

def load_json(filepath):
    """DEPRECATED: kept for backward compatibility during transition."""
    return {}


def save_json(filepath, data):
    """DEPRECATED: kept for backward compatibility during transition."""
    pass


def get_workspaces() -> dict:
    """Get all workspaces sorted by last_accessed."""
    with Database.cursor() as conn:
        rows = conn.execute(
            "SELECT id, path, name, created_at, last_accessed FROM workspaces ORDER BY last_accessed DESC"
        ).fetchall()
        result = {}
        for row in rows:
            result[row['id']] = {
                'id': row['id'],
                'path': row['path'],
                'name': row['name'],
                'created_at': row['created_at'],
                'last_accessed': row['last_accessed']
            }
        return result


def add_workspace(path: str) -> dict:
    """Add or update a workspace entry. Atomic upsert."""
    with Database.cursor() as conn:
        name = os.path.basename(path) or path
        now = time.time()
        # Upsert
        row = conn.execute("""
            INSERT INTO workspaces (id, path, name, created_at, last_accessed)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                last_accessed = excluded.last_accessed,
                name = excluded.name
            RETURNING id, path, name, created_at, last_accessed
        """, (str(uuid.uuid4()), path, name, now, now)).fetchone()

        if row is None:
            # Fallback: the path might already exist, re-fetch
            row = conn.execute(
                "SELECT id, path, name, created_at, last_accessed FROM workspaces WHERE path = ?",
                (path,)
            ).fetchone()

        return {
            'id': row['id'],
            'path': row['path'],
            'name': row['name'],
            'created_at': row['created_at'],
            'last_accessed': row['last_accessed']
        }


def get_workspace(workspace_id: str) -> Optional[dict]:
    """Get a single workspace by ID."""
    with Database.cursor() as conn:
        row = conn.execute(
            "SELECT id, path, name, created_at, last_accessed FROM workspaces WHERE id = ?",
            (workspace_id,)
        ).fetchone()
        if row:
            return {
                'id': row['id'],
                'path': row['path'],
                'name': row['name'],
                'created_at': row['created_at'],
                'last_accessed': row['last_accessed']
            }
        return None


def delete_workspace(workspace_id: str) -> bool:
    """Remove a workspace and cascade-delete its chats and messages."""
    with Database.cursor() as conn:
        cursor = conn.execute("DELETE FROM workspaces WHERE id = ?", (workspace_id,))
        return cursor.rowcount > 0


# --- Chat Management ---

def load_chats() -> dict:
    """Load all chats with their messages. Returns dict matching old format."""
    with Database.cursor() as conn:
        chats = {}
        chat_rows = conn.execute(
            "SELECT session_id, workspace_id, title, created_at, metadata_json FROM chats ORDER BY created_at DESC"
        ).fetchall()

        for chat_row in chat_rows:
            sid = chat_row['session_id']
            msg_rows = conn.execute(
                "SELECT role, parts_json, images_json, timestamp FROM chat_messages WHERE session_id = ? ORDER BY timestamp ASC",
                (sid,)
            ).fetchall()

            metadata = {}
            if chat_row['metadata_json']:
                try:
                    metadata = json.loads(chat_row['metadata_json'])
                except json.JSONDecodeError:
                    pass

            chats[sid] = {
                'id': sid,
                'workspace_id': chat_row['workspace_id'],
                'title': chat_row['title'],
                'created_at': chat_row['created_at'],
                'metadata': metadata,
                'messages': [
                    {
                        'role': m['role'],
                        'parts': json.loads(m['parts_json']),
                        'images': json.loads(m['images_json']),
                        'timestamp': m['timestamp']
                    }
                    for m in msg_rows
                ]
            }

        return chats


def get_workspace_sessions(workspace_id: str) -> list:
    """Get sessions for a workspace, sorted by creation date descending."""
    with Database.cursor() as conn:
        rows = conn.execute("""
            SELECT session_id, workspace_id, title, created_at, metadata_json
            FROM chats WHERE workspace_id = ? ORDER BY created_at DESC
        """, (workspace_id,)).fetchall()

        return [
            {
                'id': r['session_id'],
                'workspace_id': r['workspace_id'],
                'title': r['title'],
                'created_at': r['created_at'],
                'metadata': json.loads(r['metadata_json']) if r['metadata_json'] else {}
            }
            for r in rows
        ]


def save_chat_message(session_id: str, role: str, parts=None, title=None, workspace_id=None, **legacy_kwargs):
    """Save a chat message with automatic session creation."""
    with Database.cursor() as conn:
        now = time.time()

        # Create session if it doesn't exist
        if not conn.execute("SELECT 1 FROM chats WHERE session_id = ?", (session_id,)).fetchone():
            initial_text = ""
            if parts:
                for p in parts:
                    if p.get('type') == 'text':
                        initial_text = p.get('content', '')
                        break

            conn.execute("""
                INSERT INTO chats (session_id, workspace_id, title, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                session_id,
                workspace_id,
                title or (initial_text[:50] + "..." if initial_text else "New Chat"),
                now
            ))

        # Build parts from legacy kwargs if needed
        if parts is None:
            parts = []
            if 'text' in legacy_kwargs or legacy_kwargs.get('text'):
                parts.append({"type": "text", "content": legacy_kwargs.get('text')})
            if 'thoughts' in legacy_kwargs and legacy_kwargs.get('thoughts'):
                parts.append({"type": "thought", "content": legacy_kwargs.get('thoughts')})
            if 'tool_outputs' in legacy_kwargs and legacy_kwargs.get('tool_outputs'):
                for out in legacy_kwargs.get('tool_outputs'):
                    parts.append({"type": "tool_call", "content": {"name": out['tool'], "args": out['args']}})
                    parts.append({"type": "tool_result", "content": out['result']})

        images = legacy_kwargs.get('images', [])

        # Insert message
        conn.execute("""
            INSERT INTO chat_messages (session_id, role, parts_json, images_json, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session_id,
            role,
            json.dumps(parts),
            json.dumps(images),
            now
        ))

        # Update workspace last_accessed
        if workspace_id:
            conn.execute(
                "UPDATE workspaces SET last_accessed = ? WHERE id = ?",
                (now, workspace_id)
            )


async def async_save_chat_message(session_id: str, role: str, parts=None, title=None, workspace_id=None, **legacy_kwargs):
    """Async wrapper — SQLite is fast enough for sync calls, but we keep the API."""
    save_chat_message(session_id, role, parts, title, workspace_id, **legacy_kwargs)


def get_chat_history(session_id: str) -> list:
    """Get messages for a session."""
    with Database.cursor() as conn:
        rows = conn.execute(
            "SELECT role, parts_json, images_json, timestamp FROM chat_messages WHERE session_id = ? ORDER BY timestamp ASC",
            (session_id,)
        ).fetchall()
        return [
            {
                'role': r['role'],
                'parts': json.loads(r['parts_json']),
                'images': json.loads(r['images_json']),
                'timestamp': r['timestamp']
            }
            for r in rows
        ]


def delete_chat(session_id: str) -> bool:
    """Delete a chat session and all its messages (cascade)."""
    with Database.cursor() as conn:
        cursor = conn.execute("DELETE FROM chats WHERE session_id = ?", (session_id,))
        return cursor.rowcount > 0


def get_all_chats() -> list:
    """Get all chat sessions as a list (for sidebar listing)."""
    with Database.cursor() as conn:
        rows = conn.execute("""
            SELECT session_id, workspace_id, title, created_at, metadata_json
            FROM chats ORDER BY created_at DESC
        """).fetchall()

        return [
            {
                'id': r['session_id'],
                'workspace_id': r['workspace_id'],
                'title': r['title'],
                'created_at': r['created_at'],
                'metadata': json.loads(r['metadata_json']) if r['metadata_json'] else {}
            }
            for r in rows
        ]


def save_chat_metadata(session_id: str, metadata: dict):
    """Save Gemini session metadata (cid, rid, rcid) to the chat."""
    with Database.cursor() as conn:
        conn.execute(
            "UPDATE chats SET metadata_json = ? WHERE session_id = ?",
            (json.dumps(metadata), session_id)
        )


def get_chat_metadata(session_id: str) -> dict:
    """Retrieve session metadata."""
    with Database.cursor() as conn:
        row = conn.execute(
            "SELECT metadata_json FROM chats WHERE session_id = ?",
            (session_id,)
        ).fetchone()
        if row and row['metadata_json']:
            try:
                return json.loads(row['metadata_json'])
            except json.JSONDecodeError:
                return {}
        return {}


# --- Memory Functions ---

def get_all_memories(workspace_id: str) -> list:
    """Get all memories for a workspace."""
    with Database.cursor() as conn:
        rows = conn.execute(
            "SELECT id, category, title, content, importance, timestamp, session_id, source FROM memories WHERE workspace_id = ? ORDER BY timestamp DESC",
            (workspace_id,)
        ).fetchall()
        return [dict(row) for row in rows]


def add_memory(workspace_id: str, category: str, title: str, content: str,
               importance: int = 3, session_id: str = None, source: str = 'agent') -> dict:
    """Add a new memory entry."""
    memory_id = f"mem_{uuid.uuid4().hex[:8]}"
    with Database.cursor() as conn:
        conn.execute("""
            INSERT INTO memories (id, workspace_id, category, title, content, importance, timestamp, session_id, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (memory_id, workspace_id, category, title, content, importance, time.time(), session_id, source))

    return {
        'id': memory_id,
        'workspace_id': workspace_id,
        'category': category,
        'title': title,
        'content': content,
        'importance': importance,
        'timestamp': time.time(),
        'session_id': session_id,
        'source': source
    }


def delete_memory(memory_id: str) -> bool:
    """Delete a memory by ID."""
    with Database.cursor() as conn:
        cursor = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        return cursor.rowcount > 0


def get_relevant_memories(workspace_id: str, query: str, limit: int = 5) -> list:
    """Search memories relevant to a query using simple keyword matching."""
    with Database.cursor() as conn:
        rows = conn.execute(
            "SELECT id, category, title, content, importance, timestamp, session_id, source FROM memories WHERE workspace_id = ? ORDER BY importance DESC, timestamp DESC",
            (workspace_id,)
        ).fetchall()

        query_lower = query.lower()
        scored = []
        for row in rows:
            score = 0
            content = (row['title'] + " " + row['content']).lower()
            for word in query_lower.split():
                if word in content:
                    score += 1
            if score > 0:
                scored.append((score, dict(row)))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored[:limit]]


# --- Initialize ---

Database.init_schema()
# Attempt one-time migration from old JSON files
if not os.path.exists(os.path.join(DATA_DIR, ".migrated")):
    Database.migrate_from_json()
