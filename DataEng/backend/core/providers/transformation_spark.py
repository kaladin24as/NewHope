"""
Apache Spark transformation provider
"""
import os
from typing import Dict, Any, Optional
from core.interfaces import ComponentGenerator
from core.registry import ProviderRegistry
from core.manifest import ProjectContext


class SparkGenerator(ComponentGenerator):
    """Generator for Apache Spark distributed processing."""
    
    def __init__(self, env):
        super().__init__(env)
        self.context: Optional[ProjectContext] = None
    
    def generate(self, output_dir: str, config: Dict[str, Any]) -> None:
        """Generate Spark job scripts."""
        self.context = config.get("project_context")
        if not self.context:
            return
        
        # Assign ports
        self.context.get_service_port("spark-master", 7077)
        self.context.get_service_port("spark-ui", 8081)
        
        # Create spark jobs directory
        spark_dir = os.path.join(output_dir, "spark_jobs")
        os.makedirs(spark_dir, exist_ok=True)
        
        try:
            # Create example Spark job
            spark_job = """
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, avg, sum

# Initialize Spark session
spark = SparkSession.builder \\
    .appName("ETL Pipeline") \\
    .getOrCreate()

def extract_data(path):
    \"\"\"Extract data from source.\"\"\"
    df = spark.read \\
        .option("header", "true") \\
        .option("inferSchema", "true") \\
        .csv(path)
    
    print(f"Extracted {df.count()} records")
    return df

def transform_data(df):
    \"\"\"Transform data with Spark SQL.\"\"\"
    # Register as temp view
    df.createOrReplaceTempView("raw_data")
    
    # SQL transformations
    transformed = spark.sql(\"\"\"
        SELECT 
            id,
            UPPER(name) as name,
            value * 2 as doubled_value,
            date_column
        FROM raw_data
        WHERE value > 100
    \"\"\")
    
    # DataFrame transformations
    aggregated = transformed.groupBy("date_column") \\
        .agg(
            count("id").alias("total_records"),
            avg("doubled_value").alias("avg_value"),
            sum("doubled_value").alias("sum_value")
        )
    
    return aggregated

def load_data(df, output_path):
    \"\"\"Load data to destination.\"\"\"
    df.write \\
        .mode("overwrite") \\
        .parquet(output_path)
    
    print(f"Loaded data to {output_path}")

if __name__ == "__main__":
    # ETL Pipeline
    raw_df = extract_data("/data/input/*.csv")
    transformed_df = transform_data(raw_df)
    load_data(transformed_df, "/data/output/results")
    
    spark.stop()
"""
            
            with open(os.path.join(spark_dir, "etl_job.py"), 'w') as f:
                f.write(spark_job)
            
            # Create spark-submit script
            submit_script = """#!/bin/bash
# Submit Spark job to cluster

spark-submit \\
  --master spark://spark-master:7077 \\
  --deploy-mode client \\
  --driver-memory 2g \\
  --executor-memory 4g \\
  --executor-cores 2 \\
  --num-executors 2 \\
  /spark_jobs/etl_job.py
"""
            
            with open(os.path.join(spark_dir, "submit_job.sh"), 'w') as f:
                f.write(submit_script)
                
        except Exception as e:
            print(f"Error generating Spark jobs: {e}")
    
    def get_docker_service_definition(self, context: Any) -> Dict[str, Any]:
        """Returns Docker services for Spark cluster."""
        if not self.context:
            return {}
        
        master_port = self.context.get_service_port("spark-master", 7077)
        ui_port = self.context.get_service_port("spark-ui", 8081)
        
        return {
            "spark-master": {
                "image": "bitnami/spark:3.5",
                "environment": {
                    "SPARK_MODE": "master",
                    "SPARK_RPC_AUTHENTICATION_ENABLED": "no",
                    "SPARK_RPC_ENCRYPTION_ENABLED": "no",
                    "SPARK_LOCAL_STORAGE_ENCRYPTION_ENABLED": "no",
                    "SPARK_SSL_ENABLED": "no"
                },
                "ports": [
                    f"{master_port}:7077",
                    f"{ui_port}:8080"
                ],
                "volumes": [
                    "./spark_jobs:/spark_jobs",
                    "./data:/data"
                ]
            },
            "spark-worker-1": {
                "image": "bitnami/spark:3.5",
                "environment": {
                    "SPARK_MODE": "worker",
                    "SPARK_MASTER_URL": "spark://spark-master:7077",
                    "SPARK_WORKER_MEMORY": "4G",
                    "SPARK_WORKER_CORES": "2",
                    "SPARK_RPC_AUTHENTICATION_ENABLED": "no",
                    "SPARK_RPC_ENCRYPTION_ENABLED": "no"
                },
                "volumes": [
                    "./spark_jobs:/spark_jobs",
                    "./data:/data"
                ],
                "depends_on": ["spark-master"]
            },
            "spark-worker-2": {
                "image": "bitnami/spark:3.5",
                "environment": {
                    "SPARK_MODE": "worker",
                    "SPARK_MASTER_URL": "spark://spark-master:7077",
                    "SPARK_WORKER_MEMORY": "4G",
                    "SPARK_WORKER_CORES": "2",
                    "SPARK_RPC_AUTHENTICATION_ENABLED": "no",
                    "SPARK_RPC_ENCRYPTION_ENABLED": "no"
                },
                "volumes": [
                    "./spark_jobs:/spark_jobs",
                    "./data:/data"
                ],
                "depends_on": ["spark-master"]
            }
        }
    
    def get_env_vars(self, context: Any) -> Dict[str, str]:
        """Returns environment variables for Spark."""
        if not self.context:
            return {}
        
        master_port = self.context.get_service_port("spark-master", 7077)
        ui_port = self.context.get_service_port("spark-ui", 8081)
        
        return {
            "SPARK_MASTER_URL": f"spark://localhost:{master_port}",
            "SPARK_UI_URL": f"http://localhost:{ui_port}",
            "SPARK_DRIVER_MEMORY": "2g",
            "SPARK_EXECUTOR_MEMORY": "4g"
        }
    
    def get_docker_compose_volumes(self) -> Dict[str, Any]:
        return {}


# Register provider
ProviderRegistry.register("transformation", "Spark", SparkGenerator)
