
import sys
import os
import shutil

# Add backend to path to import core content
sys.path.append(os.path.abspath("backend"))

from core.engine import TemplateEngine

def test_generation():
    print("Testing Project Generation...")
    
    project_name = "TestProject"
    project_id = "test-uuid-1234"
    stack = {
        "ingestion": "DLT",
        "storage": "PostgreSQL",
        "transformation": "dbt",
        "orchestration": "Airflow"
    }
    
    engine = TemplateEngine()
    try:
        output = engine.generate(project_name, stack, project_id)
        print(f"Generation successful at: {output}")
        
        # Verify files
        expected_files = [
            "README.md",
            "ingestion_pipeline.py",
            "docker-compose.yml",
            "dbt_project/dbt_project.yml",
            "dags/pipeline_dag.py"
        ]
        
        missing = []
        for f in expected_files:
            if not os.path.exists(os.path.join(output, f)):
                missing.append(f)
                
        if missing:
            print(f"FAILED: Missing files: {missing}")
        else:
            print("SUCCESS: All expected files created.")
            
    except Exception as e:
        print(f"FAILED: Details: {e}")

if __name__ == "__main__":
    test_generation()
