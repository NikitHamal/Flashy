import json
import os
import time
import uuid

DATA_DIR = "data"
CHATS_FILE = os.path.join(DATA_DIR, "chats.json")
WORKSPACES_FILE = os.path.join(DATA_DIR, "workspaces.json")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def load_json(filepath):
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}

def save_json(filepath, data):
    """Save data to a JSON file atomically."""
    import tempfile
    
    # Create a temporary file in the same directory as the target file
    dir_name = os.path.dirname(filepath)
    fd, temp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
    
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        # Atomically rename the temporary file to the target file
        # This replaces the target file if it exists
        os.replace(temp_path, filepath)
    except Exception as e:
        print(f"Error saving JSON to {filepath}: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise

# --- Workspace Management ---

def get_workspaces():
    workspaces = load_json(WORKSPACES_FILE)
    # Sort by last_accessed
    return dict(sorted(workspaces.items(), key=lambda item: item[1].get('last_accessed', 0), reverse=True))

def add_workspace(path):
    workspaces = load_json(WORKSPACES_FILE)
    workspace_id = None
    
    # Check if exists
    for wid, data in workspaces.items():
        if data['path'] == path:
            workspace_id = wid
            break
    
    if not workspace_id:
        workspace_id = str(uuid.uuid4())
        name = os.path.basename(path) or path
        workspaces[workspace_id] = {
            "id": workspace_id,
            "path": path,
            "name": name,
            "created_at": time.time()
        }
    
    workspaces[workspace_id]['last_accessed'] = time.time()
    save_json(WORKSPACES_FILE, workspaces)
    return workspaces[workspace_id]

def get_workspace(workspace_id):
    workspaces = load_json(WORKSPACES_FILE)
    return workspaces.get(workspace_id)

def delete_workspace(workspace_id):
    """Remove a workspace and its associated chats."""
    workspaces = load_json(WORKSPACES_FILE)
    if workspace_id in workspaces:
        del workspaces[workspace_id]
        save_json(WORKSPACES_FILE, workspaces)
        
        # Also clean up associated chats
        chats = load_chats()
        to_delete = [sid for sid, chat in chats.items() if chat.get('workspace_id') == workspace_id]
        for sid in to_delete:
            del chats[sid]
        save_json(CHATS_FILE, chats)
        return True
    return False

# --- Chat Management ---

def load_chats():
    return load_json(CHATS_FILE)

def get_workspace_sessions(workspace_id):
    chats = load_chats()
    sessions = []
    for chat_id, chat in chats.items():
        if chat.get('workspace_id') == workspace_id:
            sessions.append(chat)
    # Sort by creation
    sessions.sort(key=lambda x: x.get("created_at", 0), reverse=True)
    return sessions

def save_chat_message(session_id, role, parts=None, title=None, workspace_id=None, **legacy_kwargs):
    """
    Save a chat message. 
    New format: parts is a list of {type: 'text'|'thought'|'tool_call'|'tool_result', content: ...}
    """
    chats = load_chats()
    if session_id not in chats:
        # Generate a title if not provided, from the first text part
        initial_text = ""
        if parts:
            for p in parts:
                if p['type'] == 'text':
                    initial_text = p['content']
                    break
        
        chats[session_id] = {
            "id": session_id,
            "workspace_id": workspace_id,
            "title": title or (initial_text[:50] + "..." if initial_text else "New Chat"),
            "created_at": time.time(),
            "messages": []
        }
    
    # Handle legacy format if called the old way
    if parts is None:
        parts = []
        if 'text' in legacy_kwargs or legacy_kwargs.get('text'):
            parts.append({"type": "text", "content": legacy_kwargs.get('text')})
        if 'thoughts' in legacy_kwargs and legacy_kwargs.get('thoughts'):
            parts.append({"type": "thought", "content": legacy_kwargs.get('thoughts')})
        if 'tool_outputs' in legacy_kwargs and legacy_kwargs.get('tool_outputs'):
            for out in legacy_kwargs.get('tool_outputs'):
                parts.append({
                    "type": "tool_call", 
                    "content": {"name": out['tool'], "args": out['args']}
                })
                parts.append({
                    "type": "tool_result",
                    "content": out['result']
                })

    chats[session_id]["messages"].append({
        "role": role,
        "parts": parts,
        "images": legacy_kwargs.get('images', []),
        "timestamp": time.time()
    })
    
    # Update workspace last accessed if linked
    if workspace_id:
        workspaces = load_json(WORKSPACES_FILE)
        if workspace_id in workspaces:
            workspaces[workspace_id]['last_accessed'] = time.time()
            save_json(WORKSPACES_FILE, workspaces)

    save_json(CHATS_FILE, chats)

def get_chat_history(session_id):
    chats = load_chats()
    return chats.get(session_id, {}).get("messages", [])

def delete_chat(session_id):
    chats = load_chats()
    if session_id in chats:
        del chats[session_id]
        save_json(CHATS_FILE, chats)
        return True
    return False

def get_all_chats():
     # Fallback for generic history if needed
    chats = load_chats()
    return list(chats.values())
