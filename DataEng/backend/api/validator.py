from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict

router = APIRouter()

class StackSelection(BaseModel):
    ingestion: str
    storage: str
    transformation: str
    orchestration: str

class ValidationResult(BaseModel):
    valid: bool
    issues: List[str] = []

COMPATIBILITY_MATRIX = {
    "ingestion": ["Airbyte", "DLT", "Kafka"],
    "storage": ["Snowflake", "BigQuery", "PostgreSQL"],
    "transformation": ["dbt"],
    "orchestration": ["Airflow", "Mage", "Prefect"]
}

@router.post("/validate", response_model=ValidationResult)
async def validate_stack(stack: StackSelection):
    issues = []
    
    # Simple validation rules for MVP
    if stack.ingestion not in COMPATIBILITY_MATRIX["ingestion"]:
        issues.append(f"Invalid ingestion tool: {stack.ingestion}")
    
    if stack.storage not in COMPATIBILITY_MATRIX["storage"]:
        issues.append(f"Invalid storage: {stack.storage}")
        
    if stack.transformation not in COMPATIBILITY_MATRIX["transformation"]:
        issues.append(f"Invalid transformation tool: {stack.transformation}")

    if stack.orchestration not in COMPATIBILITY_MATRIX["orchestration"]:
        issues.append(f"Invalid orchestration tool: {stack.orchestration}")

    # Specific conflict example (just for demo)
    if stack.orchestration == "Mage" and stack.transformation == "Matillion": # Hypothetical
        issues.append("Mage does not natively support Matillion in this version.")

    return ValidationResult(valid=len(issues) == 0, issues=issues)
