"""
Data Quality providers: Great Expectations, Soda
"""
import os
from typing import Dict, Any, Optional
from core.interfaces import ComponentGenerator
from core.registry import ProviderRegistry
from core.manifest import ProjectContext


class GreatExpectationsGenerator(ComponentGenerator):
    """Generator for Great Expectations data quality framework."""
    
    def __init__(self, env):
        super().__init__(env)
        self.context: Optional[ProjectContext] = None
    
    def generate(self, output_dir: str, config: Dict[str, Any]) -> None:
        """Generate Great Expectations project structure."""
        self.context = config.get("project_context")
        if not self.context:
            return
        
        # Create great_expectations directory
        ge_dir = os.path.join(output_dir, "great_expectations")
        os.makedirs(ge_dir, exist_ok=True)
        
        # Create subdirectories
        for subdir in ["expectations", "checkpoints", "plugins", "uncommitted"]:
            os.makedirs(os.path.join(ge_dir, subdir), exist_ok=True)
        
        try:
            # Create great_expectations.yml config
            ge_config = """# Great Expectations configuration

config_version: 3.0

datasources:
  postgres_datasource:
    class_name: Datasource
    execution_engine:
      class_name: SqlAlchemyExecutionEngine
      connection_string: postgresql://postgres:password@postgres:5432/warehouse
    data_connectors:
      default_inferred_data_connector:
        class_name: InferredAssetSqlDataConnector
        include_schema_name: true

stores:
  expectations_store:
    class_name: ExpectationsStore
    store_backend:
      class_name: TupleFilesystemStoreBackend
      base_directory: expectations/

  validations_store:
    class_name: ValidationsStore
    store_backend:
      class_name: TupleFilesystemStoreBackend
      base_directory: uncommitted/validations/

  evaluation_parameter_store:
    class_name: EvaluationParameterStore

  checkpoint_store:
    class_name: CheckpointStore
    store_backend:
      class_name: TupleFilesystemStoreBackend
      base_directory: checkpoints/

expectations_store_name: expectations_store
validations_store_name: validations_store
evaluation_parameter_store_name: evaluation_parameter_store
checkpoint_store_name: checkpoint_store

data_docs_sites:
  local_site:
    class_name: SiteBuilder
    store_backend:
      class_name: TupleFilesystemStoreBackend
      base_directory: uncommitted/data_docs/local_site/
    site_index_builder:
      class_name: DefaultSiteIndexBuilder
"""
            
            with open(os.path.join(ge_dir, "great_expectations.yml"), 'w') as f:
                f.write(ge_config)
            
            # Create example expectation suite
            example_suite = """from great_expectations.core import ExpectationSuite, ExpectationConfiguration

# Create expectation suite
suite = ExpectationSuite(
    expectation_suite_name="my_suite",
    data_asset_type="Dataset"
)

# Add expectations
suite.add_expectation(
    ExpectationConfiguration(
        expectation_type="expect_table_row_count_to_be_between",
        kwargs={"min_value": 1000, "max_value": 100000}
    )
)

suite.add_expectation(
    ExpectationConfiguration(
        expectation_type="expect_column_values_to_not_be_null",
        kwargs={"column": "id"}
    )
)

suite.add_expectation(
    ExpectationConfiguration(
        expectation_type="expect_column_values_to_be_unique",
        kwargs={"column": "id"}
    )
)

suite.add_expectation(
    ExpectationConfiguration(
        expectation_type="expect_column_values_to_be_in_set",
        kwargs={"column": "status", "value_set": ["active", "inactive", "pending"]}
    )
)
"""
            
            with open(os.path.join(ge_dir, "expectations", "example_suite.py"), 'w') as f:
                f.write(example_suite)
                
        except Exception as e:
            print(f"Error generating Great Expectations setup: {e}")
    
    def get_docker_service_definition(self, context: Any) -> Dict[str, Any]:
        """Great Expectations runs as part of pipelines, no separate service."""
        return {}
    
    def get_env_vars(self, context: Any) -> Dict[str, str]:
        """Returns environment variables for Great Expectations."""
        return {
            "GE_HOME": "/great_expectations"
        }
    
    def get_docker_compose_volumes(self) -> Dict[str, Any]:
        return {}


class SodaGenerator(ComponentGenerator):
    """Generator for Soda data quality testing."""
    
    def __init__(self, env):
        super().__init__(env)
        self.context: Optional[ProjectContext] = None
    
    def generate(self, output_dir: str, config: Dict[str, Any]) -> None:
        """Generate Soda configuration files."""
        self.context = config.get("project_context")
        if not self.context:
            return
        
        # Create soda directory
        soda_dir = os.path.join(output_dir, "soda")
        os.makedirs(soda_dir, exist_ok=True)
        
        try:
            # Create configuration.yml
            config_yml = """data_source postgres:
  type: postgres
  host: postgres
  port: 5432
  username: postgres
  password: ${POSTGRES_PASSWORD}
  database: warehouse
  schema: public
"""
            
            with open(os.path.join(soda_dir, "configuration.yml"), 'w') as f:
                f.write(config_yml)
            
            # Create example checks file
            checks_yml = """# Soda checks for data quality

checks for my_table:
  # Row count checks
  - row_count > 0
  - row_count < 1000000
  
  # Freshness check
  - freshness(timestamp_column) < 1d
  
  # Column checks
  - missing_count(id) = 0
  - duplicate_count(id) = 0
  - invalid_percent(email) < 5%:
      valid format: email
  
  # Numeric checks
  - min(age) >= 0
  - max(age) <= 120
  - avg(revenue) > 1000
  
  # Categorical checks
  - values in (status) must be in ['active', 'inactive', 'pending']
  
  # Schema checks
  - schema:
      fail:
        when required column missing: [id, name, created_at]
        when wrong column type:
          id: integer
          name: varchar
          created_at: timestamp
"""
            
            with open(os.path.join(soda_dir, "checks.yml"), 'w') as f:
                f.write(checks_yml)
            
            # Create scan script
            scan_script = """#!/bin/bash
# Soda scan script

# Run Soda scan
soda scan -d postgres -c configuration.yml checks.yml

# Check exit code
if [ $? -eq 0 ]; then
    echo "✓ All quality checks passed!"
else
    echo "✗ Quality checks failed!"
    exit 1
fi
"""
            
            with open(os.path.join(soda_dir, "run_scan.sh"), 'w') as f:
                f.write(scan_script)
                
        except Exception as e:
            print(f"Error generating Soda setup: {e}")
    
    def get_docker_service_definition(self, context: Any) -> Dict[str, Any]:
        """Soda runs as part of pipelines, no separate service."""
        return {}
    
    def get_env_vars(self, context: Any) -> Dict[str, str]:
        """Returns environment variables for Soda."""
        return {
            "SODA_CONFIG_PATH": "/soda/configuration.yml"
        }
    
    def get_docker_compose_volumes(self) -> Dict[str, Any]:
        return {}


# Register providers
ProviderRegistry.register("quality", "GreatExpectations", GreatExpectationsGenerator)
ProviderRegistry.register("quality", "Soda", SodaGenerator)
