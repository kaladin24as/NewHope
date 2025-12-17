from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from core.engine import TemplateEngine, VirtualFileSystem
from core.job_store import JobStore
import uuid
import os

router = APIRouter()
job_store = JobStore()

class GenerateRequest(BaseModel):
    project_name: str
    stack: dict

def run_generation_task(job_id: str, project_name: str, stack: dict):
    engine = TemplateEngine()
    try:
        # Generate files into VFS
        vfs = engine.generate(project_name, stack, job_id)
        
        # Flush VFS to disk
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        output_dir = os.path.join(base_path, "generated_projects", job_id)
        output_path = vfs.flush(output_dir)
        
        # Generate Architecture Documentation is now handled in engine.generate()
        # No need for separate Documenter call

        job_store.set_job(job_id, "completed", result={"path": output_path})
    except Exception as e:
        job_store.set_job(job_id, "failed", error=str(e))

@router.get("/providers")
async def get_providers():
    from core.registry import ProviderRegistry
    return ProviderRegistry.get_all_providers()

@router.post("/create")
async def create_project(request: GenerateRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    job_store.set_job(job_id, "pending")
    
    background_tasks.add_task(run_generation_task, job_id, request.project_name, request.stack)
    
    return {"status": "submitted", "job_id": job_id}

@router.get("/status/{job_id}")
async def get_status(job_id: str):
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
