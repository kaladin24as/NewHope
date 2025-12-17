"""
AntiGravity - Streamlit UI
==============================

Modern web interface for generating data engineering projects.
100% Python, zero JavaScript build complexity.
"""

import streamlit as st
import sys
from pathlib import Path
import requests
import io
import json

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from core.engine import TemplateEngine
from core.registry import ProviderRegistry


# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="AntiGravity - Data Project Generator",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =============================================================================
# STYLING
# =============================================================================

st.markdown("""
    <style>
    .big-title {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #00c6ff, #0072ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .subtitle {
        color: #666;
        font-size: 1.2rem;
        margin-top: 0;
    }
    .stButton>button {
        background: linear-gradient(90deg, #00c6ff, #0072ff);
        color: white;
        font-weight: bold;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 5px;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        color: #155724;
    }
    </style>
""", unsafe_allow_html=True)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def load_providers():
    """Load all available providers from registry"""
    try:
        # Import providers to trigger registration
        from core.providers import ingestion, storage, transformation, orchestration, infrastructure
        return ProviderRegistry.get_all_providers()
    except Exception as e:
        st.error(f"Error loading providers: {e}")
        return {}


def generate_architecture_diagram(stack: dict) -> str:
    """Generate Mermaid diagram based on selected stack"""
    
    diagram = """graph LR
    """
    
    # Data sources
    diagram += "    DS[Data Sources] --> "
    
    # Ingestion
    if stack.get("ingestion"):
        ingestion_tool = stack["ingestion"]
        diagram += f"ING[{ingestion_tool}]\n"
        diagram += f"    ING --> "
    else:
        diagram += "STG"
    
    # Storage
    if stack.get("storage"):
        storage_tool = stack["storage"]
        diagram += f"STG[{storage_tool}]\n"
        diagram += f"    STG --> "
    else:
        diagram += "FINAL"
    
    # Transformation
    if stack.get("transformation"):
        transform_tool = stack["transformation"]
        diagram += f"TRF[{transform_tool}]\n"
        diagram += f"    TRF --> "
    
    # Final output
    diagram += "OUT[Analytics/BI]\n"
    
    # Orchestration (oversees everything)
    if stack.get("orchestration"):
        orch_tool = stack["orchestration"]
        diagram += f"    ORCH[{orch_tool}] -.orchestrates.-> ING\n"
        diagram += f"    ORCH -.orchestrates.-> TRF\n"
    
    # Infrastructure
    if stack.get("infrastructure"):
        infra_tool = stack["infrastructure"]
        diagram += f"    INFRA[{infra_tool}] -.provisions.-> STG\n"
    
    # Styling
    diagram += """
    classDef ingestion fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef storage fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef transform fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    classDef orchestration fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef infrastructure fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    
    class ING ingestion
    class STG storage
    class TRF transform
    class ORCH orchestration
    class INFRA infrastructure
    """
    
    return diagram


def generate_project_locally(project_name: str, stack: dict):
    """Generate project using local engine"""
    try:
        import uuid
        
        engine = TemplateEngine()
        project_id = str(uuid.uuid4())
        
        with st.spinner("Generating project files..."):
            vfs = engine.generate(project_name, stack, project_id)
        
        return vfs
    except Exception as e:
        st.error(f"Generation failed: {e}")
        import traceback
        st.code(traceback.format_exc())
        return None


def generate_project_via_api(project_name: str, stack: dict):
    """Generate project by calling FastAPI backend"""
    try:
        api_url = st.session_state.get("api_url", "http://localhost:8000")
        
        with st.spinner("Sending request to backend..."):
            response = requests.post(
                f"{api_url}/api/generate",
                json={
                    "project_name": project_name,
                    "stack": stack
                },
                timeout=30
            )
        
        if response.status_code == 200:
            return response.content
        else:
            st.error(f"API Error: {response.status_code}")
            st.code(response.text)
            return None
            
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to backend API. Is it running?")
        st.info("Start the backend with: `cd backend && uvicorn main:app --reload`")
        return None
    except Exception as e:
        st.error(f"API request failed: {e}")
        return None


# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main():
    
    # Header
    st.markdown('<p class="big-title">🚀 AntiGravity</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Generate production-ready data engineering projects in seconds</p>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Integration mode
        integration_mode = st.radio(
            "Integration Mode",
            ["Local (Direct)", "API (HTTP)"],
            help="Local: Import backend directly. API: Call FastAPI backend via HTTP"
        )
        
        if integration_mode == "API (HTTP)":
            api_url = st.text_input(
                "Backend API URL",
                value="http://localhost:8000",
                help="URL of the FastAPI backend"
            )
            st.session_state["api_url"] = api_url
        
        st.markdown("---")
        
        # About
        with st.expander("ℹ️ About"):
            st.markdown("""
            **AntiGravity** is a powerful data project generator that creates
            production-ready infrastructure, pipelines, and configurations.
            
            - 🎯 Stack-agnostic
            - 🔒 Secrets management
            - 🐳 Docker-ready
            - 📊 Best practices
            """)
    
    # Main content - Two columns
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📝 Project Configuration")
        
        # Project name
        project_name = st.text_input(
            "Project Name",
            value="my_data_project",
            help="Name of your data project (alphanumeric, dashes, underscores)"
        )
        
        # Validate project name
        if not project_name.replace("_", "").replace("-", "").isalnum():
            st.warning("⚠️ Project name can only contain letters, numbers, dashes, and underscores")
        
        st.markdown("### Technology Stack")
        
        # Load providers
        if "providers" not in st.session_state:
            st.session_state.providers = load_providers()
        
        providers = st.session_state.providers
        
        # Stack selection
        stack = {}
        
        # Ingestion
        if providers.get("ingestion"):
            stack["ingestion"] = st.selectbox(
                "🔄 Ingestion",
                ["None"] + providers["ingestion"],
                help="Tool for extracting data from sources"
            )
            if stack["ingestion"] == "None":
                stack["ingestion"] = None
        
        # Storage
        if providers.get("storage"):
            stack["storage"] = st.selectbox(
                "💾 Storage / Data Warehouse",
                ["None"] + providers["storage"],
                help="Where to store your data"
            )
            if stack["storage"] == "None":
                stack["storage"] = None
        
        # Transformation
        if providers.get("transformation"):
            stack["transformation"] = st.selectbox(
                "⚙️ Transformation",
                ["None"] + providers["transformation"],
                help="Tool for transforming data (dbt, Spark, etc.)"
            )
            if stack["transformation"] == "None":
                stack["transformation"] = None
        
        # Orchestration
        if providers.get("orchestration"):
            stack["orchestration"] = st.selectbox(
                "🎼 Orchestration",
                ["None"] + providers["orchestration"],
                help="Workflow orchestration tool"
            )
            if stack["orchestration"] == "None":
                stack["orchestration"] = None
        
        # Infrastructure
        if providers.get("infrastructure"):
            stack["infrastructure"] = st.selectbox(
                "☁️ Infrastructure (IaC)",
                ["None"] + providers["infrastructure"],
                help="Infrastructure as Code tool"
            )
            if stack["infrastructure"] == "None":
                stack["infrastructure"] = None
    
    with col2:
        st.subheader("📊 Architecture Visualization")
        
        # Generate and display Mermaid diagram
        diagram = generate_architecture_diagram(stack)
        
        st.markdown(f"""
        ```mermaid
        {diagram}
        ```
        """)
        
        # Stack summary
        with st.expander("📋 Stack Summary"):
            active_tools = {k: v for k, v in stack.items() if v}
            if active_tools:
                for category, tool in active_tools.items():
                    st.markdown(f"**{category.capitalize()}:** `{tool}`")
            else:
                st.info("No tools selected yet")
    
    # Generate button
    st.markdown("---")
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
    
    with col_btn2:
        generate_button = st.button(
            "🚀 Generate Project",
            use_container_width=True,
            type="primary"
        )
    
    # Generation logic
    if generate_button:
        
        # Validate
        if not project_name:
            st.error("❌ Please enter a project name")
            return
        
        if not any(stack.values()):
            st.error("❌ Please select at least one tool from the stack")
            return
        
        # Generate
        if integration_mode == "Local (Direct)":
            vfs = generate_project_locally(project_name, stack)
            
            if vfs:
                st.success("✅ Project generated successfully!")
                
                # Display files
                with st.expander("📁 Generated Files", expanded=True):
                    files = vfs.list_files()
                    for file_path in sorted(files):
                        st.code(file_path, language="")
                
                # Download as ZIP
                st.markdown("### 📦 Download")
                zip_bytes = vfs.to_bytes_zip()
                
                st.download_button(
                    label="⬇️ Download ZIP",
                    data=zip_bytes,
                    file_name=f"{project_name}.zip",
                    mime="application/zip",
                    use_container_width=True
                )
                
                # Next steps
                st.info(f"""
                **Next Steps:**
                1. Extract the ZIP file
                2. Copy `.env.example` to `.env` and configure credentials
                3. Run `docker-compose up` to start services
                4. Start building! 🎉
                """)
        
        else:  # API mode
            zip_data = generate_project_via_api(project_name, stack)
            
            if zip_data:
                st.success("✅ Project generated successfully via API!")
                
                st.download_button(
                    label="⬇️ Download ZIP",
                    data=zip_data,
                    file_name=f"{project_name}.zip",
                    mime="application/zip",
                    use_container_width=True
                )


if __name__ == "__main__":
    main()
