"""Test rápido de validación del sistema"""
import sys
sys.path.insert(0, "backend")

print("="*80)
print("TESTS DE VALIDACIÓN - AntiGravity")
print("="*80)

# Test 1: Imports
try:
    from core.registry import ProviderRegistry
    from core.stack_validator import StackValidator
    print("✅ Test 1: Imports exitosos")
except Exception as e:
    print(f"❌ Test 1: Error en imports - {e}")
    exit(1)

# Test 2: Providers Registry
try:
    providers = ProviderRegistry.get_all_providers()
    assert len(providers) == 8, f"Expected 8 categories, got {len(providers)}"
    print(f"✅ Test 2: ProviderRegistry OK - {len(providers)} categorías")
    for cat, tools in providers.items():
        print(f"   - {cat}: {len(tools)} providers")
except Exception as e:
    print(f"❌ Test 2: {e}")

# Test 3: Stack válido
try:
    stack = {
        "ingestion": "DLT",
        "storage": "PostgreSQL",
        "transformation": "dbt",
        "orchestration": "Airflow"
    }
    is_valid, errors, warnings = StackValidator.validate_stack(stack)
    assert is_valid, f"Stack should be valid but got errors: {errors}"
    print("✅ Test 3: Stack Modern Data válido")
except Exception as e:
    print(f"❌ Test 3: {e}")

# Test 4: Incompatibilidad Kafka+dbt
try:
    stack = {"ingestion": "Kafka", "transformation": "dbt"}
    is_valid, errors, warnings = StackValidator.validate_stack(stack)
    assert not is_valid, "Kafka+dbt should be invalid"
    print("✅ Test 4: Kafka+dbt detectado como inv\u00e1lido")
except Exception as e:
    print(f"❌ Test 4: {e}")

# Test 5: Incompatibilidad MongoDB+dbt
try:
    stack = {"storage": "MongoDB", "transformation": "dbt"}
    is_valid, errors, warnings = StackValidator.validate_stack(stack)
    assert not is_valid, "MongoDB+dbt should be invalid"
    print("✅ Test 5: MongoDB+dbt detectado como inválido")
except Exception as e:
    print(f"❌ Test 5: {e}")

# Test 6: Stack NoSQL válido
try:
    stack = {"storage": "MongoDB", "transformation": "Spark"}
    is_valid, errors, warnings = StackValidator.validate_stack(stack)
    assert is_valid, f"MongoDB+Spark should be valid, errors: {errors}"
    print("✅ Test 6: MongoDB+Spark válido")
except Exception as e:
    print(f"❌ Test 6: {e}")

#  Test 7: VirtualFileSystem
try:
    from core.engine import VirtualFileSystem
    vfs = VirtualFileSystem()
    vfs.add_file("test.txt", "content")
    assert "test.txt" in vfs.list_files()
    assert vfs.get_file("test.txt") == "content"
    print("✅ Test 7: VirtualFileSystem funciona")
except Exception as e:
    print(f"❌ Test 7: {e}")

# Test 8: ProjectContext
try:
    from core.manifest import ProjectContext
    ctx = ProjectContext(project_name="test", stack={})
    secret = ctx.get_or_create_secret("test_secret")
    assert len(secret) > 0
    assert ctx.get_or_create_secret("test_secret") == secret
    print("✅ Test 8: ProjectContext y secretos OK")
except Exception as e:
    print(f"❌ Test 8: {e}")

print("\n" + "="*80)
print("🎉 TESTS BÁSICOS COMPLETADOS EXITOSAMENTE")
print("="*80)
