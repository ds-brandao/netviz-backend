from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging
import subprocess
import tempfile
import os
import base64
from datetime import datetime
import yaml
import json

from config.ingestion_config import config_manager
from .github_client import GitHubClient
from .ansible_runner import AnsibleRunner

logger = logging.getLogger(__name__)

app = FastAPI(
    title="MCP Server - Ansible Playbook Manager",
    description="MCP Server for storing playbooks in GitHub and running them via Ansible",
    version="1.0.0"
)

class PlaybookStoreRequest(BaseModel):
    playbook_name: str
    playbook_content: str
    iteration: Optional[int] = 1
    timestamp: Optional[str] = None

class PlaybookRunRequest(BaseModel):
    playbook_name: str
    device_id: str
    device_host: str
    device_user: str
    device_password: Optional[str] = None
    private_key_path: Optional[str] = None

class PlaybookResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

github_client = GitHubClient()
ansible_runner = AnsibleRunner()

@app.post("/store-playbook", response_model=PlaybookResponse)
async def store_playbook(request: PlaybookStoreRequest):
    try:
        logger.info(f"Storing playbook: {request.playbook_name}")
        
        result = await github_client.store_playbook(
            name=request.playbook_name,
            content=request.playbook_content,
            iteration=request.iteration,
            timestamp=request.timestamp
        )
        
        return PlaybookResponse(
            success=True,
            message=f"Playbook {request.playbook_name} stored successfully",
            data=result
        )
    
    except Exception as e:
        logger.error(f"Failed to store playbook {request.playbook_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run-playbook", response_model=PlaybookResponse)
async def run_playbook(request: PlaybookRunRequest, background_tasks: BackgroundTasks):
    try:
        logger.info(f"Running playbook: {request.playbook_name} on device {request.device_id}")
        
        playbook_content = await github_client.get_playbook(request.playbook_name)
        
        result = await ansible_runner.run_playbook(
            playbook_content=playbook_content,
            device_host=request.device_host,
            device_user=request.device_user,
            device_password=request.device_password,
            private_key_path=request.private_key_path
        )
        
        return PlaybookResponse(
            success=result.get("success", False),
            message=f"Playbook {request.playbook_name} execution completed",
            data=result
        )
    
    except Exception as e:
        logger.error(f"Failed to run playbook {request.playbook_name}: {str(e)}")
        return PlaybookResponse(
            success=False,
            message=f"Playbook execution failed: {str(e)}",
            data={"errors": [str(e)]}
        )

@app.get("/playbook-history/{playbook_base_name}")
async def get_playbook_history(playbook_base_name: str):
    try:
        history = await github_client.get_playbook_history(playbook_base_name)
        return PlaybookResponse(
            success=True,
            message=f"Retrieved history for {playbook_base_name}",
            data=history
        )
    
    except Exception as e:
        logger.error(f"Failed to get playbook history for {playbook_base_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    github_status = await github_client.health_check()
    ansible_status = ansible_runner.health_check()
    
    return {
        "status": "healthy" if github_status and ansible_status else "unhealthy",
        "github": github_status,
        "ansible": ansible_status,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/")
async def root():
    return {
        "message": "MCP Server - Ansible Playbook Manager",
        "version": "1.0.0",
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    
    config = config_manager.get_mcp_server_config()
    
    uvicorn.run(
        "server:app",
        host=config['host'],
        port=config['port'],
        reload=True
    )