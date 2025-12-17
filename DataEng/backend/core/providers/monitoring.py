"""
Monitoring and Observability providers: Prometheus with Grafana
"""
import os
from typing import Dict, Any, Optional
from core.interfaces import ComponentGenerator
from core.registry import ProviderRegistry
from core.manifest import ProjectContext


class PrometheusGrafanaGenerator(ComponentGenerator):
    """Generator for Prometheus + Grafana monitoring stack."""
    
    def __init__(self, env):
        super().__init__(env)
        self.context: Optional[ProjectContext] = None
    
    def generate(self, output_dir: str, config: Dict[str, Any]) -> None:
        """Generate Prometheus and Grafana configuration."""
        self.context = config.get("project_context")
        if not self.context:
            return
        
        # Assign ports
        self.context.get_service_port("prometheus", 9090)
        self.context.get_service_port("grafana-monitoring", 3002)
        
        # Create monitoring directory
        mon_dir = os.path.join(output_dir, "monitoring")
        os.makedirs(mon_dir, exist_ok=True)
        
        try:
            # Create prometheus.yml configuration
            prom_config = """global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'antigravity'
    environment: 'development'

# Scrape configurations
scrape_configs:
  # Prometheus itself
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  
  # PostgreSQL exporter (if PostgreSQL is in stack)
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
  
  # Node exporter for system metrics
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
  
  # Application metrics (FastAPI)
  - job_name: 'api'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
"""
            
            with open(os.path.join(mon_dir, "prometheus.yml"), 'w') as f:
                f.write(prom_config)
            
            # Create Grafana datasource for Prometheus
            grafana_datasource = """apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
"""
            
            with open(os.path.join(mon_dir, "grafana-datasource.yml"), 'w') as f:
                f.write(grafana_datasource)
            
            # Create example alert rules
            alert_rules = """groups:
  - name: database_alerts
    interval: 30s
    rules:
      - alert: HighDatabaseConnections
        expr: pg_stat_database_numbackends > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High number of database connections"
          description: "Database has {{ $value }} connections (threshold: 80)"
      
      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database is down"
          description: "PostgreSQL database is not responding"
  
  - name: system_alerts
    interval: 30s
    rules:
      - alert: HighCPUUsage
        expr: node_cpu_seconds_total > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage detected"
          description: "CPU usage is above 80% for 5 minutes"
      
      - alert: HighMemoryUsage
        expr: node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes < 0.2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Available memory is below 20%"
"""
            
            with open(os.path.join(mon_dir, "alerts.yml"), 'w') as f:
                f.write(alert_rules)
                
        except Exception as e:
            print(f"Error generating monitoring setup: {e}")
    
    def get_docker_service_definition(self, context: Any) -> Dict[str, Any]:
        """Returns Docker services for Prometheus + Grafana monitoring stack."""
        if not self.context:
            return {}
        
        prom_port = self.context.get_service_port("prometheus", 9090)
        grafana_port = self.context.get_service_port("grafana-monitoring", 3002)
        
        return {
            "prometheus": {
                "image": "prom/prometheus:latest",
                "ports": [f"{prom_port}:9090"],
                "volumes": [
                    "./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml",
                    "./monitoring/alerts.yml:/etc/prometheus/alerts.yml",
                    "prometheus_data:/prometheus"
                ],
                "command": [
                    "--config.file=/etc/prometheus/prometheus.yml",
                    "--storage.tsdb.path=/prometheus",
                    "--web.console.libraries=/usr/share/prometheus/console_libraries",
                    "--web.console.templates=/usr/share/prometheus/consoles"
                ]
            },
            "grafana-monitoring": {
                "image": "grafana/grafana:latest",
                "ports": [f"{grafana_port}:3000"],
                "environment": {
                    "GF_SECURITY_ADMIN_USER": "admin",
                    "GF_SECURITY_ADMIN_PASSWORD": "admin",
                    "GF_USERS_ALLOW_SIGN_UP": "false"
                },
                "volumes": [
                    "grafana_monitoring_data:/var/lib/grafana",
                    "./monitoring/grafana-datasource.yml:/etc/grafana/provisioning/datasources/prometheus.yml"
                ],
                "depends_on": ["prometheus"]
            },
            "node-exporter": {
                "image": "prom/node-exporter:latest",
                "ports": ["9100:9100"],
                "command": [
                    "--path.rootfs=/host"
                ],
                "volumes": [
                    "/:/host:ro,rslave"
                ]
            },
            "postgres-exporter": {
                "image": "prometheuscommunity/postgres-exporter:latest",
                "ports": ["9187:9187"],
                "environment": {
                    "DATA_SOURCE_NAME": "postgresql://postgres:password@postgres:5432/warehouse?sslmode=disable"
                },
                "depends_on": ["prometheus"]
            }
        }
    
    def get_env_vars(self, context: Any) -> Dict[str, str]:
        """Returns environment variables for monitoring."""
        if not self.context:
            return {}
        
        prom_port = self.context.get_service_port("prometheus", 9090)
        grafana_port = self.context.get_service_port("grafana-monitoring", 3002)
        
        return {
            "PROMETHEUS_URL": f"http://localhost:{prom_port}",
            "GRAFANA_MONITORING_URL": f"http://localhost:{grafana_port}"
        }
    
    def get_docker_compose_volumes(self) -> Dict[str, Any]:
        return {
            "prometheus_data": None,
            "grafana_monitoring_data": None
        }


# Register provider
ProviderRegistry.register("monitoring", "Prometheus", PrometheusGrafanaGenerator)
