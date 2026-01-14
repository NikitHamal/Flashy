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
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

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

def save_chat_message(session_id, role, text, title=None, images=None, tool_outputs=None, workspace_id=None):
    chats = load_chats()
    if session_id not in chats:
        chats[session_id] = {
            "id": session_id,
            "workspace_id": workspace_id,
            "title": title or (text[:50] + "..." if len(text) > 50 else text),
            "created_at": time.time(),
            "messages": []
        }
    
    chats[session_id]["messages"].append({
        "role": role,
        "text": text,
        "images": images or [],
        "tool_outputs": tool_outputs or [],
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
