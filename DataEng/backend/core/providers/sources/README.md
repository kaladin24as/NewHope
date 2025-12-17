# Data Source Connector Module

## Overview

The Data Source Connector module enables AntiGravity to extract data from external sources including APIs, databases, files, and streams. This is **Phase 1 (MVP)** focusing on REST API connectivity.

## Features

✅ **Multiple Authentication Strategies**
- API Key (header or query parameter)
- Bearer Token (JWT)
- OAuth 2.0 (Client Credentials flow)
- Basic Authentication
- No Authentication

✅ **Connection Testing**
- Verify connectivity before deployment
- Validate credentials
- Auto-discovery of API schemas (OpenAPI/Swagger)

✅ **Automatic Pipeline Generation**
- DLT-based extraction pipelines
- Configurable schedules (cron format)
- Environment variable management integration

✅ **CLI Management**
- Interactive wizard for adding sources
- List, test, and remove sources
- Beautiful terminal UI with Rich

## Quick Start

### 1. Add a Data Source

```bash
python source_cli.py add
```

Follow the interactive prompts to configure your API source.

### 2. List Configured Sources

```bash
python source_cli.py list
```

### 3. Test Connection

```bash
python source_cli.py test my_api_source
```

### 4. Generate Extraction Pipeline

The extraction pipeline is automatically generated when you create a project with the source configured.

## Usage Examples

### Example 1: Public API with No Authentication

```yaml
name: jsonplaceholder
type: api
connector: REST_API
config:
  base_url: https://jsonplaceholder.typicode.com
  endpoint: /posts
auth:
  type: none
schedule: "0 */12 * * *"  # Every 12 hours
```

### Example 2: API Key Authentication

```yaml
name: weather_api
type: api
connector: REST_API
config:
  base_url: https://api.openweathermap.org/data/2.5
  endpoint: /weather
  params:
    q: "London"
    units: "metric"
auth:
  type: api_key
  location: query  # or "header"
  key_name: appid
schedule: "0 */3 * * *"  # Every 3 hours
```

**Environment Variable:**
```bash
export WEATHER_API_API_KEY=your_api_key_here
```

### Example 3: Bearer Token (GitHub)

```yaml
name: github_api
type: api
connector: REST_API
config:
  base_url: https://api.github.com
  endpoint: /user/repos
auth:
  type: bearer
schedule: "0 0 * * *"  # Daily
```

**Environment Variable:**
```bash
export GITHUB_API_API_TOKEN=ghp_your_token_here
```

### Example 4: OAuth2 (Salesforce)

```yaml
name: salesforce_crm
type: api
connector: REST_API
config:
  base_url: https://your-instance.salesforce.com/services/data/v58.0
  endpoint: /query
  params:
    q: "SELECT Id, Name FROM Account LIMIT 100"
  data_path: "records"  # Extract nested data
auth:
  type: oauth2
  token_url: https://login.salesforce.com/services/oauth2/token
schedule: "0 0 * * *"
```

**Environment Variables:**
```bash
export SALESFORCE_CRM_CLIENT_ID=your_client_id
export SALESFORCE_CRM_CLIENT_SECRET=your_client_secret
```

## Architecture

### Core Components

```
backend/core/providers/sources/
├── __init__.py              # Package exports
├── auth.py                  # Authentication strategies
└── api_connector.py         # REST API connector

backend/core/
├── source_manager.py        # CRUD operations, persistence
└── manifest.py              # DataSource model (extended)

backend/templates/sources/
├── api_extractor.py.j2      # DLT pipeline template
└── source_config.yml.j2     # Config template

config/
├── sources.yml              # User configuration (created on first add)
└── sources.example.yml      # Example configurations

source_cli.py                # CLI interface
```

### Data Flow

```
User → CLI → SourceManager → DataSource Model → YAML Persistence
                ↓
  APIConnector → Test Connection → Validate Auth
                ↓
  Template Engine → Generate DLT Pipeline → Integrate with Project
```

## Configuration File Format

Sources are stored in `config/sources.yml`:

```yaml
sources:
  - name: unique_source_name
    type: api | database | file | stream
    connector: REST_API | PostgreSQL | S3 | Kafka
    enabled: true | false
    
    config:
      base_url: https://api.example.com
      endpoint: /data
      # ... connector-specific config
    
    auth:
      type: none | api_key | bearer | oauth2 | basic
      # ... auth-specific config
    
    schedule: "0 */6 * * *"  # Optional cron schedule
    
    metadata:
      # Optional metadata
```

## Environment Variables

After adding a source, set the required environment variables based on auth type:

| Auth Type | Required Variables |
|-----------|-------------------|
| `none` | None |
| `api_key` | `{SOURCE_NAME}_API_KEY` |
| `bearer` | `{SOURCE_NAME}_API_TOKEN` |
| `oauth2` | `{SOURCE_NAME}_CLIENT_ID`<br>`{SOURCE_NAME}_CLIENT_SECRET` |
| `basic` | `{SOURCE_NAME}_USERNAME`<br>`{SOURCE_NAME}_PASSWORD` |

**Note:** Source name is converted to UPPERCASE for env vars.

## Generated Pipeline Example

When you add a source, a DLT extraction pipeline is generated:

```python
import dlt
from dlt.sources.helpers import requests
import os

@dlt.source(name="weather_api")
def weather_api_source():
    @dlt.resource(write_disposition="append")
    def fetch_data():
        headers = {
            "Content-Type": "application/json"
        }
        
        api_key = os.getenv("WEATHER_API_API_KEY")
        params = {"appid": api_key, "q": "London"}
        
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            headers=headers,
            params=params,
            timeout=30
        )
        response.raise_for_status()
        yield response.json()
    
    return fetch_data

if __name__ == "__main__":
    pipeline = dlt.pipeline(
        pipeline_name="weather_api_pipeline",
        destination="postgres",
        dataset_name="weather_data"
    )
    
    load_info = pipeline.run(weather_api_source())
    print(load_info)
```

## Testing

Run the test suite:

```bash
# Run all source tests
pytest tests/test_sources/ -v

# Run specific test
pytest tests/test_sources/test_api_connector.py::TestAuthStrategies::test_api_key_auth_header -v
```

## Extending

### Adding a New Connector Type

1. Create a new connector class inheriting from `DataSourceConnector`:

```python
# backend/core/providers/sources/database_connector.py
from core.interfaces import DataSourceConnector

class DatabaseConnector(DataSourceConnector):
    def get_source_type(self) -> str:
        return "database"
    
    def get_auth_strategy(self) -> Dict[str, Any]:
        return {"type": "basic"}
    
    # Implement other required methods...
```

2. Register the connector:

```python
from core.registry import ProviderRegistry
ProviderRegistry.register("sources", "PostgreSQL", DatabaseConnector)
```

3. Create a template in `backend/templates/sources/database_extractor.py.j2`

4. Update `source_cli.py` to handle the new source type

## Troubleshooting

### "Missing environment variable" error

Make sure you've set the required auth environment variables:
```bash
# Check current environment
env | grep YOUR_SOURCE_NAME

# Set the variable
export YOUR_SOURCE_NAME_API_KEY=your_key_here
```

### "Connection failed" error

1. Test the URL manually: `curl https://api.example.com`
2. Check authentication credentials
3. Verify network connectivity and firewall rules
4. Use `python source_cli.py test your_source` for details diagnostics

### "requests library not installed"

```bash
pip install requests
```

## Roadmap

**Phase 2: Database Connectors** (Planned)
- PostgreSQL, MySQL, SQL Server
- Incremental extraction with watermarks
- Schema discovery from INFORMATION_SCHEMA

**Phase 3: File & Stream Connectors** (Planned)
- S3/GCS file extraction
- Kafka/Kinesis stream ingestion
- Real-time data pipelines

**Phase 4: Enterprise Features** (Planned)
- HashiCorp Vault integration
- Data lineage tracking
- Source marketplace with presets
- Streamlit UI for visual management

## Contributing

Contributions are welcome! Please:

1. Add tests for new features
2. Update documentation
3. Follow existing code style
4. Run tests before submitting: `pytest tests/test_sources/`

## License

Part of the AntiGravity Data Engineering project.
