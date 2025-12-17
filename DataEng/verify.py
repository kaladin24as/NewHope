import requests
import json
import os

def test_generate():
    url = "http://localhost:8000/api/v1/generator/create"
    payload = {
        "project_name": "VerifiedProject",
        "stack": {
            "ingestion": "Airbyte",
            "storage": "Snowflake",
            "transformation": "dbt",
            "orchestration": "Airflow"
        }
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            path = response.json().get("path")
            if path and os.path.exists(path):
                print(f"Verified: Project created at {path}")
                print("Contents:")
                for root, dirs, files in os.walk(path):
                    for file in files:
                        print(os.path.join(root, file))
            else:
                print("Error: Path returned does not exist.")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_generate()
