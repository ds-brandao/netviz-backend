from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import asyncio
import uuid
import httpx

from config.ingestion_config import config_manager
from .playbook_agent import PlaybookAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Playbook Agent API",
    description="LLM-powered Ansible playbook generation and testing agent",
    version="1.0.0"
)

class PlaybookRequest(BaseModel):
    device_id: str
    intentions: str

class PlaybookResponse(BaseModel):
    task_id: str
    status: str
    message: str

class ProcessPlaybookRequest(BaseModel):
    task_id: str
    playbook_content: str

class TaskUpdateRequest(BaseModel):
    status: str
    result: Optional[Dict[str, Any]] = None

agent = PlaybookAgent()
task_results: Dict[str, Dict[str, Any]] = {}

@app.post("/generate-playbook", response_model=PlaybookResponse)
async def generate_playbook(request: PlaybookRequest):
    try:
        task_id = str(uuid.uuid4())
        
        task_results[task_id] = {
            "status": "pending",
            "started_at": "now",
            "device_id": request.device_id,
            "intentions": request.intentions,
            "playbook_content": None,
            "iteration_count": 0,
            "result": None
        }
        
        playbook_content = await agent.generate_playbook(
            device_id=request.device_id,
            intentions=request.intentions
        )
        
        task_results[task_id]["playbook_content"] = playbook_content
        task_results[task_id]["status"] = "generated"
        
        await process_playbook_internal(task_id, playbook_content)
        
        return PlaybookResponse(
            task_id=task_id,
            status="processing",
            message="Playbook generated and processing started"
        )
    
    except Exception as e:
        logger.error(f"Failed to generate playbook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    if task_id not in task_results:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task_results[task_id]

@app.post("/iteration/{task_id}")
async def continue_iteration(task_id: str):
    if task_id not in task_results:
        raise HTTPException(status_code=404, detail="Task not found")
    
    try:
        task = task_results[task_id]
        if task["status"] not in ["failed", "error"]:
            raise HTTPException(status_code=400, detail="Task is not in failed state")
        
        task["iteration_count"] += 1
        task["status"] = "iterating"
        
        new_playbook = await agent.iterate_playbook(
            device_id=task["device_id"],
            intentions=task["intentions"],
            previous_playbook=task["playbook_content"],
            iteration=task["iteration_count"]
        )
        
        task["playbook_content"] = new_playbook
        
        await process_playbook_internal(task_id, new_playbook)
        
        return {"task_id": task_id, "status": "processing", "iteration": task["iteration_count"]}
    
    except Exception as e:
        logger.error(f"Failed to iterate on task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/task/{task_id}/update")
async def update_task_status(task_id: str, update: TaskUpdateRequest):
    if task_id not in task_results:
        raise HTTPException(status_code=404, detail="Task not found")
    
    try:
        task_results[task_id]["status"] = update.status
        if update.result:
            task_results[task_id]["result"] = update.result
        
        task = task_results[task_id]
        
        if update.status == "failed" and task["iteration_count"] < agent.max_iterations:
            await continue_iteration(task_id)
        elif update.status == "success":
            task["status"] = "completed"
            logger.info(f"Task {task_id} completed successfully")
        
        return {"task_id": task_id, "status": task_results[task_id]["status"]}
    
    except Exception as e:
        logger.error(f"Failed to update task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process/playbook")
async def process_playbook(request: ProcessPlaybookRequest):
    try:
        await process_playbook_internal(request.task_id, request.playbook_content)
        return {"task_id": request.task_id, "status": "processing"}
    
    except Exception as e:
        logger.error(f"Failed to process playbook for task {request.task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    try:
        health_status = await agent.health_check()
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {
        "message": "Playbook Agent API",
        "version": "1.0.0",
        "status": "running"
    }

async def process_playbook_internal(task_id: str, playbook_content: str):
    try:
        backend_url = config_manager.get_backend_url()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{backend_url}/process/playbook",
                json={
                    "task_id": task_id,
                    "playbook_content": playbook_content
                }
            )
            
            if response.status_code == 200:
                task_results[task_id]["status"] = "processing"
                await monitor_task_status(task_id)
            else:
                logger.error(f"Backend returned error: {response.status_code}")
                task_results[task_id]["status"] = "error"
                
    except Exception as e:
        logger.error(f"Failed to process playbook: {str(e)}")
        task_results[task_id]["status"] = "error"

async def monitor_task_status(task_id: str):
    try:
        backend_url = config_manager.get_backend_url()
        max_checks = 60
        check_interval = 5
        
        for _ in range(max_checks):
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{backend_url}/task/{task_id}")
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get("status")
                    
                    if status in ["success", "failed"]:
                        await update_task_status(task_id, TaskUpdateRequest(status=status, result=result))
                        break
                        
            await asyncio.sleep(check_interval)
            
    except Exception as e:
        logger.error(f"Failed to monitor task {task_id}: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    config = config_manager.get_api_config()
    
    uvicorn.run(
        "api:app",
        host=config.get('host', '0.0.0.0'),
        port=config.get('port', 8000),
        reload=config.get('reload', True)
    )