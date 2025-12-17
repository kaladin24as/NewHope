import sys
import os
import time
from fastapi.testclient import TestClient

# Add backend to path
sys.path.append(os.path.abspath("backend"))

from main import app
from core.job_store import JobStore

client = TestClient(app)

def test_api_async_flow():
    print("Testing API Async Flow...")
    
    payload = {
        "project_name": "AsyncProject",
        "stack": {
            "ingestion": "DLT",
            "storage": "PostgreSQL",
            "transformation": "dbt",
            "orchestration": "Airflow"
        }
    }
    
    # 1. Submit Job
    print("1. Submitting Job...")
    response = client.post("/api/v1/generator/create", json=payload)
    if response.status_code != 200:
        print(f"FAILED: Submit failed {response.status_code} - {response.text}")
        return
        
    data = response.json()
    job_id = data.get("job_id")
    status = data.get("status")
    
    print(f"   Job ID: {job_id}")
    print(f"   Initial Status: {status}")
    
    if status != "submitted" or not job_id:
        print("FAILED: Invalid response format")
        return

    # 2. Poll Status
    print("2. Polling Status...")
    max_retries = 10
    for i in range(max_retries):
        time.sleep(1)
        status_resp = client.get(f"/api/v1/generator/status/{job_id}")
        if status_resp.status_code != 200:
            print(f"   Error polling: {status_resp.status_code}")
            continue
            
        job_data = status_resp.json()
        job_status = job_data.get("status")
        print(f"   Attempt {i+1}: Status = {job_status}")
        
        if job_status == "completed":
            print("SUCCESS: Job completed.")
            print(f"   Result: {job_data.get('result')}")
            return
        elif job_status == "failed":
            print(f"FAILED: Job failed with error: {job_data.get('error')}")
            return
            
    print("FAILED: Timeout waiting for job completion")

if __name__ == "__main__":
    test_api_async_flow()
