from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
import os
from .. import storage 
from ..storage import get_workspace as get_workspace_data, add_workspace

router = APIRouter()

class WorkspaceUpdate(BaseModel):
    path: str

# We will need to inject the service to set the workspace on it
# For now, we'll assume the main app handles the service link or we pass it
# Since this is a refactor, let's keep it simple.

@router.get("/workspace")
async def get_workspace():
    # This endpoint relies on the active service state
    # We might need to move this logic to app.py or share the service instance
    pass 

@router.get("/workspaces")
async def api_get_workspaces():
    return storage.get_workspaces()

@router.delete("/workspaces/{workspace_id}")
async def api_delete_workspace(workspace_id: str):
    if storage.delete_workspace(workspace_id):
        return {"message": "Workspace deleted"}
    raise HTTPException(status_code=404, detail="Workspace not found")

@router.post("/workspaces")
async def api_add_workspace(path: str = Body(..., embed=True)):
    if not os.path.exists(path):
        raise HTTPException(status_code=400, detail="Path does not exist")
    return storage.add_workspace(path)

@router.get("/workspaces/{workspace_id}/sessions")
async def api_get_workspace_sessions(workspace_id: str):
    return storage.get_workspace_sessions(workspace_id)

@router.get("/workspace/{workspace_id}/explorer")
async def get_explorer(workspace_id: str):
    try:
        ws = get_workspace_data(workspace_id)
        if not ws:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        from ..tools import Tools
        tools = Tools(ws['path'])
        return tools.get_explorer_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workspace/{workspace_id}/plan")
async def get_plan(workspace_id: str):
    try:
        ws = get_workspace_data(workspace_id)
        if not ws:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        plan_path = os.path.join(ws['path'], "plan.md")
        if os.path.exists(plan_path):
            with open(plan_path, 'r', encoding='utf-8') as f:
                return {"content": f.read()}
        return {"content": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _run_isolated_picker():
    """Run the folder picker in a separate process to avoid thread conflicts."""
    import subprocess
    import sys
    try:
        result = subprocess.run(
            [sys.executable, "backend/picker.py"],
            capture_output=True,
            text=True,
            timeout=120
        )
        output = result.stdout.strip()
        if output == "CANCELLED":
            return None
        if output.startswith("ERROR:"):
            raise Exception(output)
        return output
    except Exception as e:
        print(f"Isolated picker error: {e}")
        return None

@router.post("/workspace/pick")
def pick_workspace():
    path = _run_isolated_picker()
    if path:
        ws = storage.add_workspace(path)
        # We need to notify service to set workspace
        return ws
    return {"message": "Cancelled"}

@router.post("/path/pick")
def api_pick_path():
    """Pick a path without adding it as a workspace."""
    path = _run_isolated_picker()
    return {"path": path}
