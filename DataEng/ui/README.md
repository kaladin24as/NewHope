# AntiGravity - Streamlit UI

Modern web interface for the AntiGravity Data Project Generator.

## Features

- 🎨 **Beautiful UI**: Modern, responsive interface built with Streamlit
- 📊 **Real-time Visualization**: See your architecture diagram as you select tools
- 🔄 **Dual Integration**: Choose between local generation or API calls
- 💾 **Instant Download**: Get your project as a ZIP file
- 🚀 **Zero Build Complexity**: Pure Python, no JavaScript required

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Running the UI

### Option 1: Standalone Mode (Local Generation)

```bash
streamlit run ui/app.py
```

This mode imports the backend directly and generates projects locally.

### Option 2: API Mode (HTTP)

1. Start the FastAPI backend:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

2. In a new terminal, start Streamlit:
   ```bash
   streamlit run ui/app.py
   ```

3. In the UI, select "API (HTTP)" mode

## Usage

1. Enter your project name
2. Select tools for each stack category:
   - **Ingestion**: DLT, Airbyte, Fivetran, etc.
   - **Storage**: PostgreSQL, Snowflake, BigQuery, etc.
   - **Transformation**: dbt, Spark, etc.
   - **Orchestration**: Airflow, Dagster, Prefect
   - **Infrastructure**: Terraform, Pulumi

3. Watch the architecture diagram update in real-time
4. Click "Generate Project"
5. Download your project as a ZIP file

## Architecture Diagram

The UI automatically generates a Mermaid diagram showing the data flow:
- Data Sources → Ingestion → Storage → Transformation → Analytics
- Orchestration tools shown as overseeing the pipeline
- Infrastructure tools shown as provisioning resources

## Configuration

### Integration Mode

- **Local (Direct)**: Fastest, imports backend modules directly
- **API (HTTP)**: More flexible, communicates with FastAPI backend

### Backend API URL

When using API mode, configure the backend URL (default: `http://localhost:8000`)

## Troubleshooting

### "Could not connect to backend API"

- Ensure the FastAPI backend is running: `cd backend && uvicorn main:app --reload`
- Check the API URL is correct (default: `http://localhost:8000`)

### "No providers found"

- Make sure all provider modules are imported correctly
- Check that providers are registered in `core/providers/__init__.py`

### Streamlit not found

```bash
pip install streamlit>=1.30.0
```

## Deployment

### Local Network

```bash
streamlit run ui/app.py --server.address 0.0.0.0 --server.port 8501
```

Access from other devices on your network at `http://YOUR_IP:8501`

### Streamlit Cloud

1. Push your code to GitHub
2. Go to [streamlit.io/cloud](https://streamlit.io/cloud)
3. Deploy from repository

## Next Steps

After generating your project:

1. Extract the ZIP file
2. Navigate to project directory
3. Copy `.env.example` to `.env`
4. Configure your credentials
5. Run `docker-compose up`
6. Start building! 🎉
