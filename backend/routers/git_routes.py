from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Optional
import os
from ..storage import get_workspace as get_workspace_data, add_workspace
from ..gemini_service import GeminiService
from ..config import load_config

router = APIRouter()

class CloneRequest(BaseModel):
    url: str
    parent_path: str
    name: Optional[str] = None

class CheckoutRequest(BaseModel):
    branch: str

class GitFileAction(BaseModel):
    path: str

class GitCommitRequest(BaseModel):
    message: str

@router.post("/git/clone")
async def api_git_clone(request: CloneRequest):
    try:
        from ..git_manager import GitManager
        
        if request.name:
            repo_name = request.name
        else:
            clean_url = request.url.strip().rstrip("/")
            repo_name = clean_url.split("/")[-1].replace(".git", "")
        
        if not repo_name:
            raise HTTPException(status_code=400, detail="Could not determine repository name from URL")
            
        target_path = os.path.join(request.parent_path, repo_name)
        
        if os.path.exists(target_path) and os.listdir(target_path):
            raise HTTPException(status_code=400, detail=f"Directory already exists and is not empty: {target_path}")
        
        git = GitManager() 
        pat = load_config().get("GITHUB_PAT")
        
        result = git.clone_repo(request.url, target_path, pat=pat)
        if "Error" in result:
            raise HTTPException(status_code=500, detail=result)
            
        ws = add_workspace(target_path)
        # Note: Setting workspace in gemini_service might need dependency injection or singleton access
        # For now, we return the workspace and let the client set it if needed, 
        # or we access the global service if we must. 
        # Ideally, GeminiService shouldn't hold global state that routes depend on implicitly for *setting*,
        # but for *getting* it's okay.
        
        return ws
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Clone error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workspace/{workspace_id}/git/checkout")
async def git_checkout(workspace_id: str, request: CheckoutRequest):
    try:
        ws = get_workspace_data(workspace_id)
        if not ws:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        from ..git_manager import GitManager
        git = GitManager(ws['path'])
        result = git.checkout(request.branch)
        
        if "Error" in result:
            raise HTTPException(status_code=400, detail=result)
            
        return {"message": f"Switched to branch {request.branch}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workspace/{workspace_id}/git/pull")
async def git_pull(workspace_id: str):
    try:
        ws = get_workspace_data(workspace_id)
        if not ws: raise HTTPException(status_code=404, detail="Workspace not found")
        from ..git_manager import GitManager
        git = GitManager(ws['path'])
        result = git.pull()
        if "failed" in result.lower(): raise HTTPException(status_code=400, detail=result)
        return {"message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workspace/{workspace_id}/git/push")
async def git_push(workspace_id: str):
    try:
        ws = get_workspace_data(workspace_id)
        if not ws: raise HTTPException(status_code=404, detail="Workspace not found")
        from ..git_manager import GitManager
        git = GitManager(ws['path'])
        pat = load_config().get("GITHUB_PAT")
        result = git.push(pat=pat)
        if "failed" in result.lower(): raise HTTPException(status_code=400, detail=result)
        return {"message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workspace/{workspace_id}/git")
async def get_git_info(workspace_id: str):
    try:
        ws = get_workspace_data(workspace_id)
        if not ws:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        from ..git_manager import GitManager
        git = GitManager(ws['path'])
        
        if not git.is_repo():
            return {"is_repo": False}
        
        return {
            "is_repo": True,
            "status": git.get_status_full(),
            "branches": git.get_branches(),
            "log": git.get_log(10)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workspace/{workspace_id}/git/stage")
async def git_stage(workspace_id: str, action: GitFileAction):
    ws = get_workspace_data(workspace_id)
    if not ws: raise HTTPException(status_code=404, detail="Workspace not found")
    from ..git_manager import GitManager
    return {"message": GitManager(ws['path']).stage_file(action.path)}

@router.post("/workspace/{workspace_id}/git/unstage")
async def git_unstage(workspace_id: str, action: GitFileAction):
    ws = get_workspace_data(workspace_id)
    if not ws: raise HTTPException(status_code=404, detail="Workspace not found")
    from ..git_manager import GitManager
    return {"message": GitManager(ws['path']).unstage_file(action.path)}

@router.post("/workspace/{workspace_id}/git/commit")
async def git_commit(workspace_id: str, req: GitCommitRequest):
    ws = get_workspace_data(workspace_id)
    if not ws: raise HTTPException(status_code=404, detail="Workspace not found")
    from ..git_manager import GitManager
    return {"message": GitManager(ws['path']).commit(req.message, stage_all=False)}
