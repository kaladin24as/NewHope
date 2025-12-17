import os
import yaml
from typing import Dict, Any, Optional, List
from core.interfaces import ComponentGenerator
from core.registry import ProviderRegistry
from core.manifest import ProjectContext, ServiceConnection

class AirflowGenerator(ComponentGenerator):
    def __init__(self, env):
        super().__init__(env)
        self.context: Optional[ProjectContext] = None
    
    def register_services(self, context: ProjectContext) -> None:
        """
        Register Airflow as an orchestration service.
        """
        self.context = context
        
        # Airflow webserver port
        airflow_port = context.get_service_port("airflow", 8080)
        
        connection = ServiceConnection(
            name="airflow",
            type="airflow",
            host="airflow",
            port=airflow_port,
            env_prefix="AIRFLOW_",
            capabilities=["orchestrator", "scheduler"],
            extra={
                "webserver_port": airflow_port
            }
        )
        context.register_connection(connection)
    
    def get_dependencies(self) -> List[str]:
        """
        Airflow can use a database for metadata but it's optional.
        """
        return []  # Database is optional, Airflow can use SQLite
    
    def validate_configuration(self, context: ProjectContext) -> tuple[bool, Optional[str]]:
        """
        Airflow is flexible and can work with most configurations.
        """
        return (True, None)
    
    def get_connection_string(self, context: ProjectContext, target_service: Optional[str] = None) -> Optional[str]:
        """
        Get Airflow webserver URL.
        """
        port = context.get_service_port("airflow", 8080)
        return f"http://airflow:{port}"

    def generate(self, output_dir: str, config: Dict[str, Any]) -> None:
        self.context = config.get("project_context")
        try:
            # 1. Render DAG
            template = self.env.get_template("orchestration/airflow_dag.py.j2")
            content = template.render(project_name=config.get("project_name", "my_project"))
            dag_dir = os.path.join(output_dir, "dags")
            os.makedirs(dag_dir, exist_ok=True)
            with open(os.path.join(dag_dir, "pipeline_dag.py"), "w") as f:
                f.write(content)

            # 2. Render Custom Dockerfile if dbt is present
            # Use service discovery instead of hardcoded checks
            if self.context:
                dbt_service = self.context.get_connection("dbt_transformation")
                if dbt_service:
                    # Find database to determine adapter
                    db_service = self.context.get_service_by_capability("warehouse")
                    if not db_service:
                        db_service = self.context.get_service_by_capability("database")
                    
                    adapter = "postgres"  # default
                    if db_service:
                        db_type = db_service.type.lower()
                        if db_type in ["postgres", "postgresql"]:
                            adapter = "postgres"
                        elif db_type == "snowflake":
                            adapter = "snowflake"
                        elif db_type == "duckdb":
                            adapter = "duckdb"
                        elif db_type == "bigquery":
                            adapter = "bigquery"

                dockerfile_tmpl = self.env.get_template("orchestration/airflow_dockerfile.j2")
                docker_content = dockerfile_tmpl.render(
                    adapter=adapter,
                    extra_pip_packages=""
                )
                with open(os.path.join(output_dir, "Dockerfile"), "w") as f:
                    f.write(docker_content)

        except Exception as e:
            print(f"Error rendering orchestration (Airflow): {e}")

    def get_docker_service_definition(self, context: Any) -> Dict[str, Any]:
        """
        Returns the Docker Compose service configuration for Airflow.
        
        Args:
            context (ProjectContext): The global project context.
        """
        if not self.context:
            return {}

        try:
            template = self.env.get_template("orchestration/airflow_compose.yml.j2")
            rendered = template.render()
            parsed = yaml.safe_load(rendered)
            services = parsed.get("services", {})
            
            # Inject Glue Variables: Connect Airflow to other stack components using service discovery
            if "airflow" in services:
                service = services["airflow"]
                env = service.setdefault("environment", {})
                
                # Auto-discover database/warehouse service
                db_service = self.context.get_service_by_capability("warehouse")
                if not db_service:
                    db_service = self.context.get_service_by_capability("database")
                
                if db_service:
                    conn_str = db_service.get_connection_string(self.context)
                    if conn_str:
                        env["DESTINATION__CREDENTIALS"] = conn_str
                        env["DATA_DB_HOST"] = db_service.host
                        env["DATA_DB_PORT"] = str(db_service.port)
                        env["DATA_DB_USER"] = db_service.credentials.get("username", "user")
                        env["DATA_DB_PASSWORD"] = db_service.credentials.get("password", "password")

                # Check for dbt using service discovery
                dbt_service = self.context.get_connection("dbt_transformation")
                if dbt_service:
                    service.pop("image", None)
                    service["build"] = "."

            return services
        except Exception as e:
            print(f"Error getting airflow service config: {e}")
            return {}
    
    def get_env_vars(self, context: Any) -> Dict[str, str]:
        """
        Returns environment variables needed for Airflow.
        
        Args:
            context (ProjectContext): The global project context.
        """
        env_vars = {
            "AIRFLOW__CORE__EXECUTOR": "LocalExecutor",
            "AIRFLOW__CORE__LOAD_EXAMPLES": "False",
            "AIRFLOW__WEBSERVER__EXPOSE_CONFIG": "True"
        }
        
        # Add database connection using service discovery
        if context:
            db_service = context.get_service_by_capability("database")
            if db_service and db_service.type.lower() in ["postgres", "postgresql"]:
                pw = db_service.credentials.get("password", "password")
                port = db_service.port
                user = db_service.credentials.get("username", "postgres")
                
                env_vars["AIRFLOW__DATABASE__SQL_ALCHEMY_CONN"] = (
                    f"postgresql://{user}:{pw}@{db_service.host}:{port}/airflow"
                )
        
        return env_vars
    
    def get_docker_compose_volumes(self) -> Dict[str, Any]:
        """Returns Docker volumes for Airflow."""
        return {}

ProviderRegistry.register("orchestration", "Airflow", AirflowGenerator)
