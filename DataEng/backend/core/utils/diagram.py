from typing import List, Dict, Any
from core.manifest import ProjectContext

def generate_architecture_diagram(context: ProjectContext, components: List[Dict[str, str]]) -> str:
    """
    Generates a Mermaid.js diagram (graph TD) showing the architecture components and their connections.
    
    Args:
        context: The project context containing global settings.
        components: A list of dicts with 'category' and 'name' keys for each selected provider.
    
    Returns:
        str: The Mermaid.js diagram definition.
    """
    
    lines = ["graph TD"]
    
    # Define standard Data Engineering flow categories
    # The order implies the data flow direction: Ingestion -> Storage -> Transformation -> BI
    flow_order = ["ingestion", "storage", "transformation", "bi"]
    
    # Map category to component name for easy lookup
    comp_map = {c['category']: c['name'] for c in components}
    
    # 1. Define Nodes with styling
    # We can add subgraphs or styles if we want, but keeping it simple for now as requested.
    for comp in components:
        name = comp['name']
        # Sanitize name for ID (remove spaces, special chars if needed)
        node_id = name.replace(" ", "_").replace("-", "_")
        # Using square brackets for standard nodes
        lines.append(f"    {node_id}[{name}]")
        
    lines.append("")
    
    # 2. Define Connections based on flow_order
    # We iterate through the standard flow and connect adjacent existing components
    
    previous_node_id = None
    
    for cat in flow_order:
        if cat in comp_map:
            name = comp_map[cat]
            node_id = name.replace(" ", "_").replace("-", "_")
            
            if previous_node_id:
                lines.append(f"    {previous_node_id} --> {node_id}")
            
            previous_node_id = node_id
            
    # 3. Handle Orchestration
    # Orchestration usually schedules Ingestion and Transformation
    if 'orchestration' in comp_map:
        orch_name = comp_map['orchestration']
        orch_id = orch_name.replace(" ", "_").replace("-", "_")
        
        # Connect to Ingestion if exists
        if 'ingestion' in comp_map:
             ingest_id = comp_map['ingestion'].replace(" ", "_").replace("-", "_")
             lines.append(f"    {orch_id} -.-> {ingest_id}")
        
        # Connect to Transformation if exists
        if 'transformation' in comp_map:
             trans_id = comp_map['transformation'].replace(" ", "_").replace("-", "_")
             lines.append(f"    {orch_id} -.-> {trans_id}")

    return "\n".join(lines)
