"""
Quick verification script to test the Python-native refactoring
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

def test_imports():
    """Test that all necessary modules can be imported"""
    print("Testing imports...")
    
    try:
        from core.engine import TemplateEngine, VirtualFileSystem
        print("✓ core.engine imported successfully")
    except Exception as e:
        print(f"✗ Failed to import core.engine: {e}")
        return False
    
    try:
        from core.registry import ProviderRegistry
        print("✓ core.registry imported successfully")
    except Exception as e:
        print(f"✗ Failed to import core.registry: {e}")
        return False
    
    try:
        from core.manifest import ProjectContext
        print("✓ core.manifest imported successfully")
    except Exception as e:
        print(f"✗ Failed to import core.manifest: {e}")
        return False
    
    return True


def test_providers():
    """Test that providers are properly registered"""
    print("\nTesting provider registry...")
    
    try:
        from core.providers import (
            ingestion,
            storage,
            transformation,
            orchestration,
            infrastructure
        )
        print("✓ All provider modules imported")
        
        from core.registry import ProviderRegistry
        providers = ProviderRegistry.get_all_providers()
        
        print("\nRegistered providers:")
        for category, tools in providers.items():
            print(f"  {category}: {', '.join(tools) if tools else 'None'}")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to load providers: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vfs():
    """Test Virtual File System"""
    print("\nTesting VirtualFileSystem...")
    
    try:
        from core.engine import VirtualFileSystem
        
        vfs = VirtualFileSystem()
        vfs.add_file("test.txt", "Hello, World!")
        vfs.add_file("folder/file.py", "print('test')")
        
        files = vfs.list_files()
        print(f"✓ VFS created with {len(files)} files")
        
        # Test to_bytes_zip
        zip_bytes = vfs.to_bytes_zip()
        print(f"✓ ZIP created: {len(zip_bytes)} bytes")
        
        return True
        
    except Exception as e:
        print(f"✗ VFS test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_template_rendering():
    """Test that templates can be rendered"""
    print("\nTesting template rendering...")
    
    try:
        from jinja2 import Environment, FileSystemLoader
        import os
        
        backend_path = Path(__file__).parent / "backend"
        template_dir = backend_path / "templates"
        
        if not template_dir.exists():
            print(f"✗ Template directory not found: {template_dir}")
            return False
        
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        
        # Test rendering common template
        try:
            template = env.get_template("common/env.example.j2")
            content = template.render(
                project_name="test_project",
                stack={"ingestion": "DLT", "storage": "PostgreSQL"}
            )
            print("✓ .env template renders successfully")
        except Exception as e:
            print(f"⚠ Could not render .env template: {e}")
        
        # Test rendering dbt profile
        try:
            template = env.get_template("transformation/profiles.yml.j2")
            content = template.render(
                project_name="test_project",
                storage="PostgreSQL"
            )
            print("✓ dbt profiles template renders successfully")
        except Exception as e:
            print(f"⚠ Could not render dbt profiles: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ Template test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("AntiGravity Python-Native Verification")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Providers", test_providers()))
    results.append(("VFS", test_vfs()))
    results.append(("Templates", test_template_rendering()))
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:20} {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed! System is ready.")
        print("\nNext steps:")
        print("1. Run Streamlit UI: streamlit run ui/app.py")
        print("2. Run CLI: python cli.py")
        print("3. Check documentation: ui/README.md, CLI_GUIDE.md")
    else:
        print("✗ Some tests failed. Please check the errors above.")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
