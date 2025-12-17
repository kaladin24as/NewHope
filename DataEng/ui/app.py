"""
AntiGravity - Enhanced Streamlit UI
====================================

Modern web interface with visual component selection,
architecture preview, and directory structure visualization.
100% Python, zero JavaScript build complexity.
"""

import streamlit as st
import sys
from pathlib import Path
import requests
import json
from typing import Dict, Any, List

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from core.engine import TemplateEngine
from core.registry import ProviderRegistry
from core.stack_validator import StackValidator
from core.secret_registry import SecretRegistry


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
# COMPONENT METADATA
# =============================================================================

COMPONENT_METADATA = {
    "ingestion": {
        "icon": "🔄",
        "title": "Ingestion",
        "description": "Extrae datos de fuentes externas",
        "color": "rgba(20, 0, 0, 0.6)",
        "border": "#ff0000",
        "tools": {
            "DLT": {
                "desc": "Data Load Tool - Pipeline declarativo",
                "ports": [],
                "env_prefix": "DLT_"
            },
            "Airbyte": {
                "desc": "Conectores pre-construidos para 300+ fuentes",
                "ports": [8000],
                "env_prefix": "AIRBYTE_"
            },
            "Fivetran": {
                "desc": "Ingesta cloud-native ETL/ELT",
                "ports": [],
                "env_prefix": "FIVETRAN_"
            },
            "Kafka": {
                "desc": "Streaming en tiempo real",
                "ports": [9092],
                "env_prefix": "KAFKA_"
            }
        }
    },
    "storage": {
        "icon": "💾",
        "title": "Storage / Warehouse",
        "description": "Almacena y consulta datos",
        "color": "rgba(20, 0, 0, 0.6)",
        "border": "#ff0000",
        "tools": {
            "PostgreSQL": {
                "desc": "Base de datos relacional OLTP/OLAP",
                "ports": [5432],
                "env_prefix": "POSTGRES_"
            },
            "Snowflake": {
                "desc": "Cloud data warehouse",
                "ports": [],
                "env_prefix": "SNOWFLAKE_"
            },
            "DuckDB": {
                "desc": "OLAP embebido, ideal para desarrollo",
                "ports": [],
                "env_prefix": "DUCKDB_"
            },
            "BigQuery": {
                "desc": "Google Cloud serverless warehouse",
                "ports": [],
                "env_prefix": "BIGQUERY_"
            },
            "Redshift": {
                "desc": "AWS data warehouse",
                "ports": [5439],
                "env_prefix": "REDSHIFT_"
            }
        }
    },
    "transformation": {
        "icon": "⚙️",
        "title": "Transformation",
        "description": "Transforma y modela datos",
        "color": "rgba(20, 0, 0, 0.6)",
        "border": "#ff0000",
        "tools": {
            "dbt": {
                "desc": "SQL-based transformation framework",
                "ports": [],
                "env_prefix": "DBT_"
            },
            "Spark": {
                "desc": "Procesamiento distribuido big data",
                "ports": [4040, 7077],
                "env_prefix": "SPARK_"
            }
        }
    },
    "orchestration": {
        "icon": "🎼",
        "title": "Orchestration",
        "description": "Orquesta workflows y pipelines",
        "color": "rgba(20, 0, 0, 0.6)",
        "border": "#ff0000",
        "tools": {
            "Airflow": {
                "desc": "Platform de orquestación programática",
                "ports": [8080],
                "env_prefix": "AIRFLOW_"
            },
            "Dagster": {
                "desc": "Orchestration basado en assets",
                "ports": [3000],
                "env_prefix": "DAGSTER_"
            },
            "Prefect": {
                "desc": "Modern workflow orchestration",
                "ports": [4200],
                "env_prefix": "PREFECT_"
            },
            "Mage": {
                "desc": "Pipeline tool con UI integrado",
                "ports": [6789],
                "env_prefix": "MAGE_"
            }
        }
    },
    "infrastructure": {
        "icon": "☁️",
        "title": "Infrastructure (IaC)",
        "description": "Provisiona infraestructura cloud",
        "color": "rgba(20, 0, 0, 0.6)",
        "border": "#ff0000",
        "tools": {
            "Terraform": {
                "desc": "IaC multi-cloud declarativo",
                "ports": [],
                "env_prefix": "TF_"
            },
            "Pulumi": {
                "desc": "IaC con lenguajes de programación",
                "ports": [],
                "env_prefix": "PULUMI_"
            }
        }
    },
    "visualization": {
        "icon": "📊",
        "title": "Visualization / BI",
        "description": "Visualiza y analiza datos",
        "color": "rgba(20, 0, 0, 0.6)",
        "border": "#ff0000",
        "tools": {
            "Metabase": {
                "desc": "BI open-source fácil de usar",
                "ports": [3000],
                "env_prefix": "MB_"
            },
            "Superset": {
                "desc": "Platform BI empresarial",
                "ports": [8088],
                "env_prefix": "SUPERSET_"
            },
            "Tableau": {
                "desc": "BI enterprise líder",
                "ports": [],
                "env_prefix": "TABLEAU_"
            }
        }
    },
    "quality": {
        "icon": "✅",
        "title": "Data Quality",
        "description": "Valida calidad de datos",
        "color": "rgba(20, 0, 0, 0.6)",
        "border": "#ff0000",
        "tools": {
            "Great Expectations": {
                "desc": "Framework de validación de datos",
                "ports": [],
                "env_prefix": "GE_"
            },
            "Soda": {
                "desc": "Data quality checks como código",
                "ports": [],
                "env_prefix": "SODA_"
            }
        }
    },
    "monitoring": {
        "icon": "📈",
        "title": "Monitoring",
        "description": "Monitorea pipelines y sistemas",
        "color": "rgba(20, 0, 0, 0.6)",
        "border": "#ff0000",
        "tools": {
            "Prometheus": {
                "desc": "Métricas y alerting",
                "ports": [9090],
                "env_prefix": "PROMETHEUS_"
            },
            "Grafana": {
                "desc": "Dashboards de observabilidad",
                "ports": [3000],
                "env_prefix": "GRAFANA_"
            },
            "DataDog": {
                "desc": "Observabilidad cloud completa",
                "ports": [],
                "env_prefix": "DATADOG_"
            }
        }
    }
}


# =============================================================================
# TRON-STYLE FUTURISTIC STYLING - RED & BLACK NEON
# =============================================================================

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap');
    
    /* Global Dark Theme */
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a0000 100%);
        color: #ff3333;
        font-family: 'Orbitron', sans-serif;
    }
    
    /* Animated Grid Background */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            linear-gradient(rgba(255, 0, 0, 0.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255, 0, 0, 0.05) 1px, transparent 1px);
        background-size: 50px 50px;
        z-index: 0;
        pointer-events: none;
    }
    
    /* Main Title - Glowing Red */
    .big-title {
        font-size: 4.5rem;
        font-weight: 900;
        background: linear-gradient(90deg, #ff0000, #ff3333, #ff6666, #ff0000);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 0.3rem;
        animation: neonPulse 3s ease-in-out infinite;
        text-shadow: 
            0 0 10px rgba(255, 0, 0, 0.8),
            0 0 20px rgba(255, 0, 0, 0.6),
            0 0 30px rgba(255, 0, 0, 0.4),
            0 0 40px rgba(255, 0, 0, 0.2);
        filter: drop-shadow(0 0 20px #ff0000);
    }
    
    @keyframes neonPulse {
        0%, 100% { 
            filter: brightness(1) drop-shadow(0 0 20px #ff0000);
        }
        50% { 
            filter: brightness(1.3) drop-shadow(0 0 40px #ff0000);
        }
    }
    
    @keyframes borderGlow {
        0%, 100% { 
            box-shadow: 0 0 5px #ff0000, 0 0 10px #ff0000, inset 0 0 5px rgba(255, 0, 0, 0.2);
        }
        50% { 
            box-shadow: 0 0 10px #ff0000, 0 0 20px #ff0000, 0 0 30px #ff0000, inset 0 0 10px rgba(255, 0, 0, 0.3);
        }
    }
    
    /* Subtitle */
    .subtitle {
        color: #ff6666;
        font-size: 1.4rem;
        margin-top: 0;
        text-align: center;
        margin-bottom: 2rem;
        font-family: 'Share Tech Mono', monospace;
        text-shadow: 0 0 10px rgba(255, 0, 0, 0.5);
    }
    
    /* Component Cards - Tron Style */
    .component-card {
        padding: 1.5rem;
        border-radius: 4px;
        border: 2px solid #ff0000;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, rgba(0, 0, 0, 0.9) 0%, rgba(20, 0, 0, 0.8) 100%);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
        box-shadow: 
            0 0 5px rgba(255, 0, 0, 0.5),
            inset 0 0 10px rgba(255, 0, 0, 0.1);
    }
    
    .component-card::before {
        content: '';
        position: absolute;
        top: -2px;
        left: -2px;
        right: -2px;
        bottom: -2px;
        background: linear-gradient(45deg, #ff0000, transparent, #ff0000);
        border-radius: 4px;
        z-index: -1;
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .component-card:hover {
        transform: translateY(-4px) scale(1.02);
        box-shadow: 
            0 0 20px rgba(255, 0, 0, 0.8),
            0 0 40px rgba(255, 0, 0, 0.4),
            inset 0 0 20px rgba(255, 0, 0, 0.2);
        border-color: #ff3333;
    }
    
    .component-card:hover::before {
        opacity: 0.3;
    }
    
    .component-card-selected {
        border-width: 3px;
        border-color: #ff0000;
        background: linear-gradient(135deg, rgba(20, 0, 0, 0.95) 0%, rgba(40, 0, 0, 0.9) 100%);
        animation: borderGlow 2s ease-in-out infinite;
    }
    
    /* Section Headers */
    .section-header {
        font-size: 2.2rem;
        font-weight: 700;
        margin-top: 2rem;
        margin-bottom: 1.5rem;
        color: #ff3333;
        text-transform: uppercase;
        letter-spacing: 0.2rem;
        text-align: center;
        text-shadow: 
            0 0 10px rgba(255, 0, 0, 0.8),
            0 0 20px rgba(255, 0, 0, 0.4);
        border-bottom: 2px solid #ff0000;
        padding-bottom: 0.5rem;
    }
    
    /* Preview Box */
    .preview-box {
        background: linear-gradient(135deg, rgba(0, 0, 0, 0.8) 0%, rgba(20, 0, 0, 0.6) 100%);
        border: 2px solid #ff0000;
        border-radius: 4px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 
            0 0 10px rgba(255, 0, 0, 0.3),
            inset 0 0 20px rgba(255, 0, 0, 0.1);
    }
    
    /* Connection Items */
    .connection-item {
        padding: 1rem;
        background: linear-gradient(90deg, rgba(20, 0, 0, 0.9) 0%, rgba(0, 0, 0, 0.8) 100%);
        border-left: 4px solid #ff0000;
        margin: 0.8rem 0;
        border-radius: 4px;
        box-shadow: 
            0 0 10px rgba(255, 0, 0, 0.3),
            inset 0 0 10px rgba(255, 0, 0, 0.1);
        transition: all 0.3s ease;
        color: #ff6666;
    }
    
    .connection-item:hover {
        border-left-width: 6px;
        box-shadow: 
            0 0 20px rgba(255, 0, 0, 0.5),
            inset 0 0 15px rgba(255, 0, 0, 0.2);
        transform: translateX(5px);
    }
    
    /* Buttons - Neon Red */
    .stButton>button {
        background: linear-gradient(135deg, #ff0000 0%, #cc0000 100%) !important;
        color: #000000 !important;
        font-weight: 900 !important;
        font-family: 'Orbitron', sans-serif !important;
        border: 2px solid #ff3333 !important;
        padding: 1rem 3rem !important;
        border-radius: 4px !important;
        font-size: 1.3rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.15rem !important;
        box-shadow: 
            0 0 10px rgba(255, 0, 0, 0.5),
            0 0 20px rgba(255, 0, 0, 0.3),
            inset 0 0 10px rgba(255, 50, 50, 0.2) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #ff3333 0%, #ff0000 100%) !important;
        box-shadow: 
            0 0 20px rgba(255, 0, 0, 0.8),
            0 0 40px rgba(255, 0, 0, 0.5),
            inset 0 0 20px rgba(255, 100, 100, 0.3) !important;
        transform: scale(1.05) !important;
        color: #ffffff !important;
    }
    
    /* Input Fields */
    .stTextInput>div>div>input {
        background-color: rgba(0, 0, 0, 0.8) !important;
        color: #ff3333 !important;
        border: 2px solid #ff0000 !important;
        border-radius: 4px !important;
        font-family: 'Share Tech Mono', monospace !important;
        box-shadow: inset 0 0 10px rgba(255, 0, 0, 0.2) !important;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #ff3333 !important;
        box-shadow: 
            0 0 10px rgba(255, 0, 0, 0.5),
            inset 0 0 15px rgba(255, 0, 0, 0.3) !important;
    }
    
    /* Radio Buttons */
    .stRadio > label {
        color: #ff6666 !important;
        font-family: 'Orbitron', sans-serif !important;
        text-shadow: 0 0 5px rgba(255, 0, 0, 0.3);
    }
    
    .stRadio > div {
        background-color: rgba(0, 0, 0, 0.5) !important;
        border: 1px solid #ff0000 !important;
        border-radius: 4px !important;
        padding: 0.5rem !important;
    }
    
    /* Sidebar */
    .css-1d391kg, [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #000000 0%, #1a0000 100%) !important;
        border-right: 2px solid #ff0000 !important;
        box-shadow: 0 0 20px rgba(255, 0, 0, 0.3) !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: rgba(20, 0, 0, 0.8) !important;
        color: #ff3333 !important;
        border: 1px solid #ff0000 !important;
        border-radius: 4px !important;
        font-family: 'Orbitron', sans-serif !important;
    }
    
    /* Code Blocks */
    .stCodeBlock {
        background-color: rgba(0, 0, 0, 0.9) !important;
        border: 1px solid #ff0000 !important;
        border-radius: 4px !important;
        box-shadow: inset 0 0 10px rgba(255, 0, 0, 0.2) !important;
    }
    
    code {
        color: #ff6666 !important;
        font-family: 'Share Tech Mono', monospace !important;
    }
    
    /* Markdown */
    .stMarkdown {
        color: #ff9999 !important;
    }
    
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #ff3333 !important;
        text-shadow: 0 0 10px rgba(255, 0, 0, 0.5);
    }
    
    /* Horizontal Rule */
    hr {
        border-color: #ff0000 !important;
        box-shadow: 0 0 5px rgba(255, 0, 0, 0.5);
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        background: #000000;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(0, 0, 0, 0.5);
        border: 1px solid #330000;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #ff0000, #cc0000);
        border-radius: 4px;
        box-shadow: 0 0 5px rgba(255, 0, 0, 0.5);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #ff3333, #ff0000);
        box-shadow: 0 0 10px rgba(255, 0, 0, 0.8);
    }
    
    /* Alerts and Info Boxes */
    .stAlert {
        background-color: rgba(20, 0, 0, 0.8) !important;
        border: 2px solid #ff0000 !important;
        border-radius: 4px !important;
        color: #ff6666 !important;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #ff0000 !important;
    }
    
    /* Tool Badge */
    .tool-badge {
        display: inline-block;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        margin: 0.3rem;
        background: linear-gradient(135deg, rgba(255, 0, 0, 0.2) 0%, rgba(0, 0, 0, 0.8) 100%);
        border: 1px solid #ff0000;
        color: #ff6666;
        font-family: 'Share Tech Mono', monospace;
        box-shadow: 0 0 5px rgba(255, 0, 0, 0.3);
    }
    
    /* Success/Warning Messages */
    .stSuccess {
        background-color: rgba(0, 20, 0, 0.8) !important;
        border: 2px solid #00ff00 !important;
        color: #00ff00 !important;
    }
    
    .stWarning {
        background-color: rgba(30, 15, 0, 0.8) !important;
        border: 2px solid #ffaa00 !important;
        color: #ffaa00 !important;
    }
    
    .stError {
        background-color: rgba(30, 0, 0, 0.8) !important;
        border: 2px solid #ff0000 !important;
        color: #ff3333 !important;
    }
    </style>
""", unsafe_allow_html=True)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def load_providers():
    """Load all available providers from registry"""
    try:
        from core.providers import (
            ingestion, storage, transformation, 
            orchestration, infrastructure, visualization,
            quality, monitoring
        )
        return ProviderRegistry.get_all_providers()
    except Exception as e:
        st.error(f"Error loading providers: {e}")
        return {}


def render_component_card(category: str, metadata: dict, providers: List[str], selected_value: str, current_stack: Dict[str, str] = None):
    """Render a visual component card with selection and compatibility filtering"""
    
    icon = metadata["icon"]
    title = metadata["title"]
    description = metadata["description"]
    color = metadata["color"]
    border = metadata["border"]
    
    # Filter providers based on compatibility
    if current_stack:
        compatible_providers = StackValidator.suggest_compatible_options(current_stack, category)
        # Keep only compatible providers
        providers = [p for p in providers if p in compatible_providers]
    
    # Card styling
    card_class = "component-card"
    if selected_value and selected_value != "None":
        card_class += " component-card-selected"
    
    st.markdown(f"""
        <div class="component-card" style="background-color: {color}; border-color: {border};">
            <h3>{icon} {title}</h3>
            <p style="color: #666; margin-bottom: 1rem;">{description}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Selection
    options = ["None"] + providers
    selected = st.radio(
        f"Selecciona {title}:",
        options,
        key=f"radio_{category}",
        horizontal=False,
        label_visibility="collapsed"
    )
    
    # Show tool details if selected
    if selected != "None" and selected in metadata["tools"]:
        tool_info = metadata["tools"][selected]
        st.markdown(f"**{selected}**: {tool_info['desc']}")
        if tool_info["ports"]:
            ports_str = ", ".join([f":{p}" for p in tool_info["ports"]])
            st.caption(f"🔌 Puertos: {ports_str}")
    
    return selected if selected != "None" else None


def generate_architecture_diagram(stack: Dict[str, str]) -> str:
    """Generate enhanced Mermaid diagram with interconnections"""
    
    diagram = """graph TB
    """
    
    # Data sources
    diagram += "    DS[📁 Data Sources]\n"
    
    # Build flow based on selected components
    prev_node = "DS"
    
    # Ingestion
    if stack.get("ingestion"):
        tool = stack["ingestion"]
        metadata = COMPONENT_METADATA["ingestion"]["tools"].get(tool, {})
        ports = metadata.get("ports", [])
        port_label = f":{ports[0]}" if ports else ""
        diagram += f"    ING[🔄 {tool}{port_label}]\n"
        diagram += f"    {prev_node} -->|extract| ING\n"
        prev_node = "ING"
    
    # Storage
    if stack.get("storage"):
        tool = stack["storage"]
        metadata = COMPONENT_METADATA["storage"]["tools"].get(tool, {})
        ports = metadata.get("ports", [])
        port_label = f":{ports[0]}" if ports else ""
        diagram += f"    STG[💾 {tool}{port_label}]\n"
        diagram += f"    {prev_node} -->|load| STG\n"
        prev_node = "STG"
    
    # Transformation
    if stack.get("transformation"):
        tool = stack["transformation"]
        metadata = COMPONENT_METADATA["transformation"]["tools"].get(tool, {})
        ports = metadata.get("ports", [])
        port_label = f":{ports[0]}" if ports else ""
        diagram += f"    TRF[⚙️ {tool}{port_label}]\n"
        diagram += f"    STG -->|transform| TRF\n"
        diagram += f"    TRF -->|write back| STG\n"
    
    # Final output
    diagram += "    OUT[📊 Analytics/BI]\n"
    diagram += f"    STG -->|query| OUT\n" if stack.get("storage") else f"    {prev_node} --> OUT\n"
    
    # Orchestration (connects to multiple nodes)
    if stack.get("orchestration"):
        tool = stack["orchestration"]
        metadata = COMPONENT_METADATA["orchestration"]["tools"].get(tool, {})
        ports = metadata.get("ports", [])
        port_label = f":{ports[0]}" if ports else ""
        diagram += f"    ORCH[🎼 {tool}{port_label}]\n"
        if stack.get("ingestion"):
            diagram += "    ORCH -.schedule.-> ING\n"
        if stack.get("transformation"):
            diagram += "    ORCH -.schedule.-> TRF\n"
    
    # Infrastructure
    if stack.get("infrastructure"):
        tool = stack["infrastructure"]
        diagram += f"    INFRA[☁️ {tool}]\n"
        if stack.get("storage"):
            diagram += "    INFRA -.provision.-> STG\n"
    
    # Visualization
    if stack.get("visualization"):
        tool = stack["visualization"]
        metadata = COMPONENT_METADATA["visualization"]["tools"].get(tool, {})
        ports = metadata.get("ports", [])
        port_label = f":{ports[0]}" if ports else ""
        diagram += f"    VIZ[📊 {tool}{port_label}]\n"
        if stack.get("storage"):
            diagram += "    STG -->|connect| VIZ\n"
    
    # Quality
    if stack.get("quality"):
        tool = stack["quality"]
        diagram += f"    QA[✅ {tool}]\n"
        if stack.get("storage"):
            diagram += "    QA -.validate.-> STG\n"
        if stack.get("transformation"):
            diagram += "    QA -.test.-> TRF\n"
    
    # Monitoring
    if stack.get("monitoring"):
        tool = stack["monitoring"]
        metadata = COMPONENT_METADATA["monitoring"]["tools"].get(tool, {})
        ports = metadata.get("ports", [])
        port_label = f":{ports[0]}" if ports else ""
        diagram += f"    MON[📈 {tool}{port_label}]\n"
        diagram += "    MON -.observe.-> ING\n" if stack.get("ingestion") else ""
        diagram += "    MON -.observe.-> STG\n" if stack.get("storage") else ""
        diagram += "    MON -.observe.-> TRF\n" if stack.get("transformation") else ""
    
    # Styling
    diagram += """
    classDef ingestion fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef storage fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef transform fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    classDef orchestration fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef infrastructure fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef visualization fill:#e0f2f1,stroke:#004d40,stroke-width:2px
    classDef quality fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef monitoring fill:#e3f2fd,stroke:#0d47a1,stroke-width:2px
    
    class ING ingestion
    class STG storage
    class TRF transform
    class ORCH orchestration
    class INFRA infrastructure
    class VIZ visualization
    class QA quality
    class MON monitoring
    """
    
    return diagram


def generate_directory_tree(project_name: str, stack: Dict[str, str]) -> str:
    """Generate directory tree preview based on selected stack"""
    
    tree = f"📁 {project_name}/\n"
    tree += "├── 📄 .env.example\n"
    tree += "├── 📄 .gitignore\n"
    tree += "├── 📄 docker-compose.yml\n"
    tree += "├── 📄 README.md\n"
    
    if stack.get("ingestion"):
        tool = stack["ingestion"]
        tree += "├── 📁 ingestion/\n"
        tree += "│   ├── 📄 ingestion_pipeline.py\n"
        tree += f"│   ├── 📄 Dockerfile.ingestion\n"
        tree += "│   └── 📄 requirements.txt\n"
    
    if stack.get("storage"):
        tool = stack["storage"]
        tree += "├── 📁 storage/\n"
        tree += "│   ├── 📄 init.sql\n"
        tree += "│   └── 📄 schema.sql\n"
    
    if stack.get("transformation"):
        tool = stack["transformation"]
        if tool == "dbt":
            tree += "├── 📁 dbt_project/\n"
            tree += "│   ├── 📄 dbt_project.yml\n"
            tree += "│   ├── 📄 profiles.yml\n"
            tree += "│   ├── 📁 models/\n"
            tree += "│   │   ├── 📄 staging/\n"
            tree += "│   │   └── 📄 marts/\n"
            tree += "│   └── 📁 tests/\n"
        else:
            tree += f"├── 📁 transformation/\n"
            tree += f"│   └── 📄 transform.py\n"
    
    if stack.get("orchestration"):
        tool = stack["orchestration"]
        tree += f"├── 📁 orchestration/\n"
        if tool == "Airflow":
            tree += "│   ├── 📁 dags/\n"
            tree += "│   │   └── 📄 main_dag.py\n"
            tree += "│   └── 📄 airflow.cfg\n"
        else:
            tree += f"│   └── 📄 {tool.lower()}_config.py\n"
    
    if stack.get("infrastructure"):
        tool = stack["infrastructure"]
        tree += "├── 📁 terraform/\n"
        tree += "│   ├── 📄 main.tf\n"
        tree += "│   ├── 📄 variables.tf\n"
        tree += "│   └── 📄 outputs.tf\n"
    
    if stack.get("visualization"):
        tree += "├── 📁 visualization/\n"
        tree += "│   └── 📄 config.yml\n"
    
    if stack.get("quality"):
        tree += "├── 📁 quality/\n"
        tree += "│   ├── 📄 expectations.yml\n"
        tree += "│   └── 📄 tests.py\n"
    
    if stack.get("monitoring"):
        tree += "├── 📁 monitoring/\n"
        tree += "│   ├── 📄 prometheus.yml\n"
        tree += "│   └── 📄 alerts.yml\n"
    
    tree += "└── 📁 docs/\n"
    tree += "    ├── 📄 ARCHITECTURE.md\n"
    tree += "    └── 📄 SETUP.md\n"
    
    return tree


def show_interconnections(stack: Dict[str, str]):
    """Show how components interconnect"""
    
    st.markdown("### 🔗 Interconexiones de Componentes")
    
    connections = []
    
    # Ingestion -> Storage
    if stack.get("ingestion") and stack.get("storage"):
        ing_tool = stack["ingestion"]
        stg_tool = stack["storage"]
        stg_meta = COMPONENT_METADATA["storage"]["tools"].get(stg_tool, {})
        port = stg_meta.get("ports", [5432])[0] if stg_meta.get("ports") else "N/A"
        
        connections.append({
            "from": f"🔄 {ing_tool}",
            "to": f"💾 {stg_tool}",
            "type": "Data Load",
            "protocol": f"Port {port}",
            "env_vars": [f"{stg_meta.get('env_prefix', '')}HOST", 
                        f"{stg_meta.get('env_prefix', '')}PORT",
                        f"{stg_meta.get('env_prefix', '')}DATABASE"]
        })
    
    # Storage -> Transformation
    if stack.get("storage") and stack.get("transformation"):
        stg_tool = stack["storage"]
        trf_tool = stack["transformation"]
        stg_meta = COMPONENT_METADATA["storage"]["tools"].get(stg_tool, {})
        
        connections.append({
            "from": f"💾 {stg_tool}",
            "to": f"⚙️ {trf_tool}",
            "type": "Transform",
            "protocol": "SQL Connection",
            "env_vars": [f"DBT_HOST", "DBT_PORT", "DBT_DATABASE"]
        })
    
    # Orchestration -> All
    if stack.get("orchestration"):
        orch_tool = stack["orchestration"]
        orchestrated = []
        if stack.get("ingestion"):
            orchestrated.append(f"🔄 {stack['ingestion']}")
        if stack.get("transformation"):
            orchestrated.append(f"⚙️ {stack['transformation']}")
        
        if orchestrated:
            connections.append({
                "from": f"🎼 {orch_tool}",
                "to": " + ".join(orchestrated),
                "type": "Schedule",
                "protocol": "DAG Execution",
                "env_vars": ["AIRFLOW__CORE__EXECUTOR", "AIRFLOW__CORE__SQL_ALCHEMY_CONN"]
            })
    
    # Storage -> Visualization
    if stack.get("storage") and stack.get("visualization"):
        stg_tool = stack["storage"]
        viz_tool = stack["visualization"]
        
        connections.append({
            "from": f"💾 {stg_tool}",
            "to": f"📊 {viz_tool}",
            "type": "Query",
            "protocol": "Read-Only Connection",
            "env_vars": ["DATABASE_URL", "DB_CONNECTION_STRING"]
        })
    
    # Display connections
    if connections:
        for conn in connections:
            with st.container():
                st.markdown(f"""
                    <div class="connection-item">
                        <strong>{conn['from']}</strong> → <strong>{conn['to']}</strong>
                        <br/>
                        <small>Tipo: {conn['type']} | Protocolo: {conn['protocol']}</small>
                    </div>
                """, unsafe_allow_html=True)
                
                with st.expander("Variables de Entorno"):
                    for var in conn['env_vars']:
                        st.code(var, language="")
        
        # Network info
        st.info("🌐 **Red Docker**: Todos los servicios se comunican via `antigravity_net`")
    else:
        st.info("Selecciona componentes para ver sus interconexiones")


def generate_project_locally(project_name: str, stack: dict):
    """Generate project using local engine"""
    try:
        import uuid
        
        engine = TemplateEngine()
        project_id = str(uuid.uuid4())
        
        with st.spinner("Generando archivos del proyecto..."):
            vfs = engine.generate(project_name, stack, project_id)
        
        return vfs
    except Exception as e:
        st.error(f"Error en generación: {e}")
        import traceback
        st.code(traceback.format_exc())
        return None


# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main():
    
    # Header
    st.markdown('<p class="big-title">🚀 AntiGravity</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Genera proyectos de ingeniería de datos production-ready en segundos</p>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        # Project name
        project_name = st.text_input(
            "Nombre del Proyecto",
            value="my_data_project",
            help="Nombre del proyecto (alphanumeric, dashes, underscores)"
        )
        
        # Validate
        if not project_name.replace("_", "").replace("-", "").isalnum():
            st.warning("⚠️ Solo letras, números, guiones y guiones bajos")
        
        st.markdown("---")
        
        # Integration mode
        integration_mode = st.radio(
            "Modo de Integración",
            ["Local (Directo)", "API (HTTP)"],
            help="Local: Importa backend directamente. API: Llama a FastAPI via HTTP"
        )
        
        if integration_mode == "API (HTTP)":
            api_url = st.text_input(
                "URL del Backend",
                value="http://localhost:8000"
            )
            st.session_state["api_url"] = api_url
        
        st.markdown("---")
        
        # About
        with st.expander("ℹ️ Acerca de"):
            st.markdown("""
            **AntiGravity** genera proyectos de datos production-ready:
            
            - 🎯 Stack-agnostic
            - 🔒 Gestión de secretos
            - 🐳 Docker-ready
            - 📊 Mejores prácticas
            - 🚀 100% Python
            """)
    
    # Main layout
    st.markdown('<div class="section-header">📦 Selección de Componentes</div>', unsafe_allow_html=True)
    
    # Load providers
    if "providers" not in st.session_state:
        st.session_state.providers = load_providers()
    
    providers = st.session_state.providers
    
    # Component selection in columns
    col1, col2 = st.columns(2)
    
    stack = {}
    
    with col1:
        # Core components
        for category in ["ingestion", "storage", "transformation"]:
            if category in providers and providers[category]:
                metadata = COMPONENT_METADATA.get(category, {})
                selected = render_component_card(
                    category,
                    metadata,
                    providers[category],
                    stack.get(category),
                    current_stack=stack  # Pass current stack for filtering
                )
                if selected:
                    stack[category] = selected
                st.markdown("---")
    
    with col2:
        # Supporting components
        for category in ["orchestration", "infrastructure", "visualization", "quality", "monitoring"]:
            if category in providers and providers[category]:
                metadata = COMPONENT_METADATA.get(category, {})
                selected = render_component_card(
                    category,
                    metadata,
                    providers[category],
                    stack.get(category),
                    current_stack=stack  # Pass current stack for filtering
                )
                if selected:
                    stack[category] = selected
                st.markdown("---")
    
    # =========================================================================
    # VALIDATION SECTION
    # =========================================================================
    
    # Remove None values
    active_stack = {k: v for k, v in stack.items() if v}
    
    if active_stack:
        st.markdown("---")
        st.markdown('<div class="section-header">🔍 Validación de Stack</div>', unsafe_allow_html=True)
        
        # Validate stack
        is_valid, errors, warnings = StackValidator.validate_stack(active_stack)
        
        col_val1, col_val2 = st.columns(2)
        
        with col_val1:
            if is_valid:
                st.success("✅ Stack válido - sin incompatibilidades")
            else:
                st.error(f"❌ Stack inválido - {len(errors)} error(es)")
            
            # Show errors  
            if errors:
                with st.expander("❌ Errores", expanded=True):
                    for error in errors:
                        st.error(error)
            
            # Show warnings
            if warnings:
                with st.expander(f"⚠️ Advertencias ({len(warnings)})"):
                    for warning in warnings:
                        st.warning(warning)
        
        with col_val2:
            # Preview secrets
            try:
                secrets = SecretRegistry.get_secrets_for_stack(active_stack, project_name)
                st.info(f"🔐 Se generarán **{len(secrets)} secrets** automáticamente")
                
                with st.expander("🔑 Preview de Secrets"):
                    secret_examples = list(secrets.keys())[:8]  # Show first 8
                    for secret in secret_examples:
                        st.code(f"{secret}: {'*' * 16}", language="")
                    if len(secrets) > 8:
                        st.caption(f"... y {len(secrets) - 8} más")
            except Exception as e:
                st.warning(f"No se pudo generar preview de secrets: {e}")
    
    # Preview Section
    st.markdown("---")
    st.markdown('<div class="section-header">👁️ Vista Previa</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🏗️ Arquitectura", "📁 Estructura", "🔗 Conexiones"])
    
    with tab1:
        st.markdown("### Diagrama de Arquitectura")
        diagram = generate_architecture_diagram(stack)
        st.markdown(f"""
        ```mermaid
        {diagram}
        ```
        """)
    
    with tab2:
        st.markdown("### Estructura de Directorios")
        tree = generate_directory_tree(project_name, stack)
        st.code(tree, language="")
    
    with tab3:
        show_interconnections(stack)
    
    # Generate button
    st.markdown("---")
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
    
    with col_btn2:
        active_components = sum(1 for v in stack.values() if v)
        button_disabled = active_components == 0
        
        if button_disabled:
            st.warning("⚠️ Selecciona al menos un componente")
        
        generate_button = st.button(
            f"🚀 Generar Proyecto ({active_components} componentes)",
            use_container_width=True,
            type="primary",
            disabled=button_disabled
        )
    
    # Generation logic
    if generate_button:
        if not project_name:
            st.error("❌ Ingresa un nombre de proyecto")
            return
        
        # Generate
        vfs = generate_project_locally(project_name, stack)
        
        if vfs:
            st.success("✅ ¡Proyecto generado exitosamente!")
            
            # Display files
            with st.expander("📁 Archivos Generados", expanded=True):
                files = vfs.list_files()
                for file_path in sorted(files):
                    st.code(file_path, language="")
            
            # Download
            st.markdown("### 📦 Descargar")
            zip_bytes = vfs.to_bytes_zip()
            
            st.download_button(
                label="⬇️ Descargar ZIP",
                data=zip_bytes,
                file_name=f"{project_name}.zip",
                mime="application/zip",
                use_container_width=True
            )
            
            # Next steps
            st.info(f"""
            **Próximos Pasos:**
            1. Extrae el archivo ZIP
            2. Copia `.env.example` a `.env` y configura credenciales
            3. Ejecuta `docker-compose up` para iniciar servicios
            4. ¡Comienza a construir! 🎉
            """)


if __name__ == "__main__":
    main()
