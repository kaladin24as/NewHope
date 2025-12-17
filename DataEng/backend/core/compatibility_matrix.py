"""
Compatibility Matrix for AntiGravity DataEng
Defines all compatibility rules between providers across categories.
"""

from typing import Dict, List, Set, Optional


# =============================================================================
# COMPATIBILITY MATRIX
# =============================================================================

COMPATIBILITY_MATRIX = {
    # =========================================================================
    # INGESTION COMPATIBILITY
    # =========================================================================
    "ingestion": {
        "DLT": {
            "compatible_storage": ["PostgreSQL", "Snowflake", "BigQuery", "DuckDB", "Redshift"],
            "compatible_transformation": ["dbt", "Spark"],
            "compatible_orchestration": ["Airflow", "Prefect", "Dagster", "Mage"],
            "incompatible_with": [],
            "description": "Python-native data loading tool, works with most SQL warehouses"
        },
        "Airbyte": {
            "compatible_storage": ["PostgreSQL", "Snowflake", "BigQuery", "Redshift", "MongoDB"],
            "compatible_transformation": ["dbt", "Spark"],
            "compatible_orchestration": ["Airflow", "Prefect", "Dagster"],
            "incompatible_with": [],
            "description": "Open-source ELT platform with 300+ connectors"
        },
        "Kafka": {
            "compatible_storage": ["PostgreSQL", "MongoDB", "BigQuery"],
            "compatible_transformation": ["Spark"],  # Only streaming
            "compatible_orchestration": ["Airflow"],
            "incompatible_with": ["dbt"],
            "warning": "Kafka is streaming-focused. Use Spark for transformations, not dbt (batch).",
            "description": "Real-time streaming platform"
        }
    },
    
    # =========================================================================
    # STORAGE COMPATIBILITY
    # =========================================================================
    "storage": {
        "PostgreSQL": {
            "compatible_visualization": ["Metabase", "Superset", "Grafana"],
            "compatible_quality": ["Great Expectations", "Soda"],
            "compatible_monitoring": ["Prometheus"],
            "works_with_all": True,
            "type": "sql",
            "deployment": "on-premise",
            "description": "Open-source relational database, works with everything"
        },
        "Snowflake": {
            "compatible_visualization": ["Metabase", "Superset", "Grafana"],
            "compatible_quality": ["Great Expectations", "Soda"],
            "compatible_monitoring": [],
            "type": "sql",
            "deployment": "cloud",
            "requires_cloud": True,
            "warning": "Cloud warehouse - ensure Terraform infrastructure is selected",
            "description": "Cloud data warehouse"
        },
        "BigQuery": {
            "compatible_visualization": ["Metabase", "Superset", "Grafana"],
            "compatible_quality": ["Great Expectations", "Soda"],
            "compatible_monitoring": [],
            "type": "sql",
            "deployment": "cloud",
            "requires_cloud": True,
            "requires_service_account": True,
            "warning": "GCP BigQuery requires service account credentials",
            "description": "Google Cloud data warehouse"
        },
        "Redshift": {
            "compatible_visualization": ["Metabase", "Superset", "Grafana"],
            "compatible_quality": ["Great Expectations", "Soda"],
            "compatible_monitoring": [],
            "type": "sql",
            "deployment": "cloud",
            "requires_cloud": True,
            "warning": "AWS Redshift - ensure Terraform infrastructure is selected",
            "description": "AWS data warehouse"
        },
        "DuckDB": {
            "compatible_visualization": ["Metabase", "Grafana"],
            "compatible_quality": ["Great Expectations", "Soda"],
            "compatible_monitoring": [],
            "type": "sql",
            "deployment": "embedded",
            "warning": "DuckDB is embedded/local - not recommended for production BI at scale",
            "description": "Embedded analytics database"
        },
        "MongoDB": {
            "compatible_visualization": ["Superset", "Grafana"],
            "compatible_quality": ["Soda"],
            "compatible_monitoring": ["Prometheus"],
            "incompatible_with": ["dbt", "Great Expectations"],
            "type": "nosql",
            "deployment": "on-premise",
            "warning": "NoSQL database - limited SQL transformation support",
            "description": "NoSQL document database"
        }
    },
    
    # =========================================================================
    # TRANSFORMATION COMPATIBILITY
    # =========================================================================
    "transformation": {
        "dbt": {
            "requires_sql_storage": True,
            "compatible_storage": ["PostgreSQL", "Snowflake", "BigQuery", "Redshift", "DuckDB"],
            "incompatible_with": ["MongoDB", "Kafka"],
            "type": "sql",
            "paradigm": "batch",
            "description": "SQL-based transformation tool for analytics"
        },
        "Spark": {
            "compatible_storage": ["PostgreSQL", "Snowflake", "BigQuery", "MongoDB"],
            "supports_streaming": True,
            "compatible_with_kafka": True,
            "type": "distributed",
            "paradigm": "batch_and_streaming",
            "description": "Distributed processing engine for big data"
        }
    },
    
    # =========================================================================
    # ORCHESTRATION COMPATIBILITY
    # =========================================================================
    "orchestration": {
        "Airflow": {
            "works_with_all": True,
            "has_monitoring": True,
            "description": "Most popular workflow orchestration platform"
        },
        "Prefect": {
            "works_with_all": True,
            "cloud_option": True,
            "description": "Modern workflow orchestration with cloud option"
        },
        "Dagster": {
            "works_with_all": True,
            "asset_focused": True,
            "description": "Asset-based data orchestrator"
        },
        "Mage": {
            "works_with_all": True,
            "has_ui": True,
            "description": "Data pipeline tool with integrated UI"
        }
    },
    
    # =========================================================================
    # INFRASTRUCTURE COMPATIBILITY
    # =========================================================================
    "infrastructure": {
        "Terraform": {
            "works_with_all": True,
            "supports": ["AWS", "GCP", "Azure"],
            "recommended_for": ["Snowflake", "BigQuery", "Redshift"],
            "description": "Infrastructure as Code for cloud resources"
        }
    },
    
    # =========================================================================
    # VISUALIZATION COMPATIBILITY
    # =========================================================================
    "visualization": {
        "Metabase": {
            "compatible_storage": ["PostgreSQL", "Snowflake", "BigQuery", "Redshift", "DuckDB", "MongoDB"],
            "requires": ["storage"],
            "type": "self-service-bi",
            "description": "Easy-to-use BI tool"
        },
        "Superset": {
            "compatible_storage": ["PostgreSQL", "Snowflake", "BigQuery", "Redshift", "MongoDB"],
            "requires": ["storage"],
            "type": "enterprise-bi",
            "description": "Apache open-source BI platform"
        },
        "Grafana": {
            "compatible_storage": ["PostgreSQL", "Prometheus"],
            "use_case": "metrics_visualization",
            "type": "dashboards",
            "description": "Metrics and monitoring dashboards"
        }
    },
    
    # =========================================================================
    # QUALITY COMPATIBILITY
    # =========================================================================
    "quality": {
        "Great Expectations": {
            "compatible_storage": ["PostgreSQL", "Snowflake", "BigQuery", "Redshift", "DuckDB"],
            "requires": ["storage"],
            "type": "sql",
            "description": "Data validation and testing framework"
        },
        "Soda": {
            "compatible_storage": ["PostgreSQL", "Snowflake", "BigQuery", "Redshift", "DuckDB", "MongoDB"],
            "requires": ["storage"],
            "supports_nosql": True,
            "type": "sql_and_nosql",
            "description": "Data quality checks as code"
        }
    },
    
    # =========================================================================
    # MONITORING COMPATIBILITY
    # =========================================================================
    "monitoring": {
        "Prometheus": {
            "works_with_all": True,
            "exports_available": {
                "PostgreSQL": "postgres_exporter",
                "MongoDB": "mongodb_exporter",
                "Airflow": "statsd_exporter"
            },
            "description": "Metrics collection and alerting"
        }
    }
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_provider_info(category: str, provider: str) -> Optional[Dict]:
    """Get information about a specific provider."""
    return COMPATIBILITY_MATRIX.get(category, {}).get(provider)


def is_compatible(provider1_cat: str, provider1: str, provider2_cat: str, provider2: str) -> bool:
    """
    Check if two providers are compatible.
    
    Args:
        provider1_cat: Category of first provider (e.g., "ingestion")
        provider1: Name of first provider (e.g., "DLT")
        provider2_cat: Category of second provider (e.g., "storage")
        provider2: Name of second provider (e.g., "PostgreSQL")
    
    Returns:
        True if compatible, False otherwise
    """
    info1 = get_provider_info(provider1_cat, provider1)
    info2 = get_provider_info(provider2_cat, provider2)
    
    if not info1 or not info2:
        return False
    
    # Check if provider1 explicitly lists provider2 as incompatible
    if provider2 in info1.get("incompatible_with", []):
        return False
    
    # Check if provider2 explicitly lists provider1 as incompatible
    if provider1 in info2.get("incompatible_with", []):
        return False
    
    # Check specific compatibility lists
    compat_key = f"compatible_{provider2_cat}"
    if compat_key in info1:
        return provider2 in info1[compat_key]
    
    # Check reverse
    compat_key_reverse = f"compatible_{provider1_cat}"
    if compat_key_reverse in info2:
        return provider1 in info2[compat_key_reverse]
    
    # Check if either works with all
    if info1.get("works_with_all") or info2.get("works_with_all"):
        return True
    
    return True  # Default to compatible if no rules found


def get_compatible_providers(category: str, current_stack: Dict[str, str]) -> List[str]:
    """
    Get list of compatible providers for a category given current stack.
    
    Args:
        category: Category to get providers for
        current_stack: Current stack configuration
    
    Returns:
        List of compatible provider names
    """
    all_providers = list(COMPATIBILITY_MATRIX.get(category, {}).keys())
    compatible = []
    
    for provider in all_providers:
        is_compat = True
        
        # Check against all selected providers in stack
        for selected_cat, selected_prov in current_stack.items():
            if not is_compatible(category, provider, selected_cat, selected_prov):
                is_compat = False
                break
        
        if is_compat:
            compatible.append(provider)
    
    return compatible
