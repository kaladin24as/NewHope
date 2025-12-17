"""
Core providers package.

This module must be imported to trigger provider registration.
"""

# Import all providers to trigger registration with ProviderRegistry
from . import ingestion
from . import ingestion_extended  # Additional ingestion providers (Airbyte)
from . import ingestion_streaming  # Streaming ingestion (Kafka)
from . import storage
from . import storage_extended  # Additional storage providers (Snowflake, DuckDB)
from . import storage_cloud  # Cloud storage providers (BigQuery, Redshift, MongoDB)
from . import transformation
from . import transformation_spark  # Spark transformation
from . import orchestration
from . import orchestration_extended  # Additional orchestration (Prefect, Dagster)
from . import orchestration_mage  # Mage AI orchestration
from . import infrastructure
from . import visualization  # NEW: Phase 3 - BI tools
from . import quality  # NEW: Phase 3 - Data quality
from . import monitoring  # NEW: Phase 3 - Monitoring

__all__ = [
    'ingestion',
    'ingestion_extended',
    'ingestion_streaming',
    'storage',
    'storage_extended',
    'storage_cloud',
    'transformation',
    'transformation_spark',
    'orchestration',
    'orchestration_extended',
    'orchestration_mage',
    'infrastructure',
    'visualization',
   'quality',
    'monitoring'
]
