from typing import Dict, Any

class JobStore:
    _instance = None
    _jobs: Dict[str, Dict[str, Any]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(JobStore, cls).__new__(cls)
        return cls._instance

    def set_job(self, job_id: str, status: str, result: Any = None, error: str = None):
        self._jobs[job_id] = {
            "status": status,
            "result": result,
            "error": error
        }

    def get_job(self, job_id: str) -> Dict[str, Any]:
        return self._jobs.get(job_id)
