"""
Test script for Python-Native migrated AntiGravity
Generates a test project and verifies generated files
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from core.engine import TemplateEngine
from core.registry import ProviderRegistry

# Load providers
import backend.core.providers.ingestion
import backend.core.providers.storage
import backend.core.providers.transformation
import backend.core.providers.orchestration
import backend.core.providers.infrastructure

def test_full_stack_generation():
    """Test generating a project with full stack"""
    
    print("=" * 80)
    print("Testing Python-Native AntiGravity - Full Stack Generation")
    print("=" * 80)
    
    # Define test stack
    test_stack = {
        "ingestion": "dlt",
        "storage": "postgres",
        "transformation": "dbt",
        "orchestration": "airflow",
        "infrastructure": None
    }
    
    project_name = "test-python-native-platform"
    project_id = "test123"
    
    print(f"\n📦 Generating project: {project_name}")
    print(f"Stack configuration:")
    for category, tool in test_stack.items():
        print(f"  • {category}: {tool or 'None'}")
    
    # Generate project
    engine = TemplateEngine()
    vfs = engine.generate(project_name, test_stack, project_id)
    
    generated_files = vfs.list_files()
    print(f"\n✅ Generated {len(generated_files)} files:")
    for file_path in sorted(generated_files):
        print(f"  📄 {file_path}")
    
    # Verify critical files exist
    critical_files = [
        "README.md",
        "docker-compose.yml",
        "Makefile",
        ".devcontainer/devcontainer.json",
        "ARCHITECTURE.md"
    ]
    
    print("\n🔍 Verifying critical files...")
    all_present = True
    for critical_file in critical_files:
        if critical_file in generated_files:
            print(f"  ✓ {critical_file}")
        else:
            print(f"  ✗ MISSING: {critical_file}")
            all_present = False
    
    # Flush to disk
    output_path = os.path.join(os.getcwd(), "generated_projects", project_name)
    vfs.flush(output_path)
    
    print(f"\n💾 Project written to: {output_path}")
    
    # Verify Makefile content
    makefile_content = vfs.get_file("Makefile")
    if makefile_content:
        print("\n📜 Makefile contains:")
        if "dbt-run" in makefile_content:
            print("  ✓ dbt tasks (dbt-run, dbt-test, dbt-docs)")
        if "airflow-init" in makefile_content:
            print("  ✓ Airflow initialization")
        if "make help" in makefile_content or ".PHONY: help" in makefile_content:
            print("  ✓ Help command")
    
    # Verify devcontainer
    devcontainer_content = vfs.get_file(".devcontainer/devcontainer.json")
    if devcontainer_content:
        print("\n🐳 DevContainer configuration present:")
        if "dbt-power-user" in devcontainer_content:
            print("  ✓ dbt Power User extension")
        if "ms-python.python" in devcontainer_content:
            print("  ✓ Python extension")
    
    print("\n" + "=" * 80)
    if all_present:
        print("✅ TEST PASSED: All critical files generated successfully!")
    else:
        print("❌ TEST FAILED: Some critical files are missing!")
    print("=" * 80)
    
    return all_present

if __name__ == "__main__":
    try:
        success = test_full_stack_generation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
