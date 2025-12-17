"""
Test Suite Exhaustivo para AntiGravity
Valida orquestación completa del sistema
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from core.registry import ProviderRegistry
from core.stack_validator import StackValidator
from core.manifest import ProjectContext, ServiceConnection
from core.engine import TemplateEngine, VirtualFileSystem
from core.compatibility_matrix import is_compatible, get_compatible_providers

print("=" * 80)
print("🧪 SUITE DE TESTS EXHAUSTIVA - AntiGravity DataEng")
print("=" * 80)

# Stats
total_tests = 0
passed_tests = 0
failed_tests = 0

def test(name, condition, error_msg=""):
    """Helper function to run a test"""
    global total_tests, passed_tests, failed_tests
    total_tests += 1
    if condition:
        print(f"✅ Test {total_tests}: {name}")
        passed_tests += 1
        return True
    else:
        print(f"❌ Test {total_tests}: {name}")
        if error_msg:
            print(f"   Error: {error_msg}")
        failed_tests += 1
        return False

print("\n" + "=" * 80)
print("📦 TESTS DE PROVIDER REGISTRY")
print("=" * 80)

# Test 1: Provider Registry tiene todas las categorías
providers = ProviderRegistry.get_all_providers()
test("ProviderRegistry tiene 8 categorías", len(providers) == 8)

# Test 2: Cada categoría tiene providers
for category, tools in providers.items():
    test(f"Categoría '{category}' tiene providers", len(tools) > 0, f"Found: {tools}")

# Test 3: Providers específicos están registrados
test("PostgreSQL está registrado", "PostgreSQL" in providers.get("storage", []))
test("DLT está registrado", "DLT" in providers.get("ingestion", []))
test("dbt está registrado", "dbt" in providers.get("transformation", []))
test("Airflow está registrado", "Airflow" in providers.get("orchestration", []))

print("\n" + "=" * 80)
print("🔒 TESTS DE VALIDACIÓN DE STACKS")
print("=" * 80)

# Test 4: Stack válido básico
stack_valid = {
    "ingestion": "DLT",
    "storage": "PostgreSQL",
    "transformation": "dbt",
    "orchestration": "Airflow"
}
is_valid, errors, warnings = StackValidator.validate_stack(stack_valid)
test("Stack Modern Data es válido", is_valid and len(errors) == 0, f"Errors: {errors}")

# Test 5: Incompatibilidad Kafka + dbt
stack_invalid_kafka_dbt = {
    "ingestion": "Kafka",
    "transformation": "dbt"
}
is_valid, errors, warnings = StackValidator.validate_stack(stack_invalid_kafka_dbt)
test("Kafka + dbt es marcado como inválido", not is_valid, f"Should be invalid but got: {errors}")

# Test 6: Incompatibilidad MongoDB + dbt
stack_invalid_mongo_dbt = {
    "storage": "MongoDB",
    "transformation": "dbt"
}
is_valid, errors, warnings = StackValidator.validate_stack(stack_invalid_mongo_dbt)
test("MongoDB + dbt es marcado como inválido", not is_valid, f"Should be invalid but got: {errors}")

# Test 7: Incompatibilidad MongoDB + Great Expectations
stack_invalid_mongo_ge = {
    "storage": "MongoDB",
    "quality": "Great Expectations"
}
is_valid, errors, warnings = StackValidator.validate_stack(stack_invalid_mongo_ge)
test("MongoDB + Great Expectations es marcado como inválido", not is_valid)

# Test 8: Stack NoSQL válido
stack_nosql = {
    "storage": "MongoDB",
    "transformation": "Spark",
    "quality": "Soda"
}
is_valid, errors, warnings = StackValidator.validate_stack(stack_nosql)
test("Stack NoSQL (MongoDB+Spark+Soda) es válido", is_valid, f"Errors: {errors}")

# Test 9: Warning DuckDB + BI
stack_duckdb = {
    "storage": "DuckDB",
    "visualization": "Superset"
}
is_valid, errors, warnings = StackValidator.validate_stack(stack_duckdb)
test("DuckDB + Superset genera warning pero es válido", is_valid and len(warnings) > 0)

print("\n" + "=" * 80)
print("🔗 TESTS DE COMPATIBILITY MATRIX")
print("=" * 80)

# Test 10: DLT es compatible con PostgreSQL
test("DLT es compatible con PostgreSQL", 
     is_compatible("ingestion", "DLT", "storage", "PostgreSQL"))

# Test 11: dbt es compatible con Snowflake
test("dbt es compatible con Snowflake", 
     is_compatible("transformation", "dbt", "storage", "Snowflake"))

# Test 12: Kafka NO es compatible con dbt
test("Kafka NO es compatible con dbt", 
     not is_compatible("ingestion", "Kafka", "transformation", "dbt"))

# Test 13: MongoDB NO es compatible con dbt
test("MongoDB NO es compatible con dbt",
     not is_compatible("storage", "MongoDB", "transformation", "dbt"))

# Test 14: Spark es compatible con MongoDB
test("Spark es compatible con MongoDB",
     is_compatible("transformation", "Spark", "storage", "MongoDB"))

print("\n" + "=" * 80)
print("🎯 TESTS DE PROJECT CONTEXT")
print("=" * 80)

# Test 15: ProjectContext creation
context = ProjectContext(project_name="test_project", stack=stack_valid)
test("ProjectContext se crea correctamente", context.project_name == "test_project")

# Test 16: Secret generation
secret = context.get_or_create_secret("test_secret")
test("ProjectContext genera secretos", secret is not None and len(secret) > 0)

# Test 17: Secret persistence
secret2 = context.get_or_create_secret("test_secret")
test("Secretos son persistentes", secret == secret2)

# Test 18: Port management
port = context.get_service_port("test_service", 5432)
test("ProjectContext asigna puertos", port == 5432)

# Test 19: Service registration
connection = ServiceConnection(
    name="test_db",
    type="postgres",
    host="localhost",
    port=5432,
    env_prefix="DB_",
    capabilities=["database", "sql_database"]
)
context.register_connection(connection)
test("ProjectContext registra servicios", len(context.connections) == 1)

# Test 20: Service discovery by capability
db_service = context.get_service_by_capability("database")
test("Service discovery funciona", db_service is not None and db_service.name == "test_db")

print("\n" + "=" * 80)
print("💾 TESTS DE VIRTUAL FILE SYSTEM")
print("=" * 80)

# Test 21: VFS creation
vfs = VirtualFileSystem()
test("VirtualFileSystem se crea correctamente", vfs is not None)

# Test 22: Add file to VFS
vfs.add_file("README.md", "# Test Project")
test("VFS acepta archivos", "README.md" in vfs.list_files())

# Test 23: Get file from VFS
content = vfs.get_file("README.md")
test("VFS retorna contenido correcto", content == "# Test Project")

# Test 24: Multiple files
vfs.add_file("docker-compose.yml", "version: '3.8'")
vfs.add_file(".env", "DB_HOST=localhost")
test("VFS maneja múltiples archivos", len(vfs.list_files()) == 3)

print("\n" + "=" * 80)
print("🏭 TESTS DE GENERACIÓN DE PROYECTOS")
print("=" * 80)

try:
    # Test 25: Template Engine creation
    engine = TemplateEngine()
    test("TemplateEngine se crea correctamente", engine is not None)
    
    # Test 26: Basic project generation
    print("\n📝 Generando proyecto de prueba...")
    test_stack = {
        "ingestion": "DLT",
        "storage": "PostgreSQL",
        "transformation": "dbt",
        "orchestration": "Airflow"
    }
    
    vfs_generated = engine.generate("test_project", test_stack, "test-123")
    test("Generación de proyecto completa sin errores", vfs_generated is not None)
    
    # Test 27: Generated files
    files = vfs_generated.list_files()
    test("Proyecto generado tiene archivos", len(files) > 0, f"Files: {len(files)}")
    
    # Test 28: README generated
    test("README.md fue generado", "README.md" in files)
    
    # Test 29: docker-compose.yml generated
    test("docker-compose.yml fue generado", "docker-compose.yml" in files)
    
    # Test 30: .env files generated
    env_files = [f for f in files if ".env" in f]
    test("Archivos .env fueron generados", len(env_files) > 0, f"Found: {env_files}")
    
    # Test 31: ARCHITECTURE.md generated
    test("ARCHITECTURE.md fue generado", "ARCHITECTURE.md" in files)
    
except Exception as e:
    print(f"❌ Error en generación de proyecto: {e}")
    failed_tests += 5  # Tests 25-30

print("\n" + "=" * 80)
print("🧪 TESTS DE STACKS COMPLEJOS")
print("=" * 80)

# Test 32: Enterprise Cloud Stack
enterprise_stack = {
    "ingestion": "Airbyte",
    "storage": "Snowflake",
    "transformation": "dbt",
    "orchestration": "Airflow",
    "infrastructure": "Terraform",
    "visualization": "Superset",
    "quality": "Soda"
}
is_valid, errors, warnings = StackValidator.validate_stack(enterprise_stack)
test("Stack Enterprise Cloud es válido", is_valid, f"Errors: {errors}")

# Test 33: Streaming Stack
streaming_stack = {
    "ingestion": "Kafka",
    "storage": "PostgreSQL",
    "transformation": "Spark",
    "orchestration": "Airflow"
}
is_valid, errors, warnings = StackValidator.validate_stack(streaming_stack)
test("Stack Streaming (Kafka+Spark) es válido", is_valid, f"Errors: {errors}")

# Test 34: Full Stack
full_stack = {
    "ingestion": "DLT",
    "storage": "PostgreSQL",
    "transformation": "dbt",
    "orchestration": "Airflow",
    "infrastructure": "Terraform",
    "visualization": "Metabase",
    "quality": "Great Expectations",
    "monitoring": "Prometheus"
}
is_valid, errors, warnings = StackValidator.validate_stack(full_stack)
test("Stack completo (8 componentes) es válido", is_valid, f"Errors: {errors}")

print("\n" + "=" * 80)
print("🔍 TESTS DE SUGERENCIAS DE COMPATIBILIDAD")
print("=" * 80)

# Test 35: Sugerencias para transformation con PostgreSQL
current = {"storage": "PostgreSQL"}
suggestions = StackValidator.suggest_compatible_options(current, "transformation")
test("PostgreSQL sugiere dbt y Spark", "dbt" in suggestions and "Spark" in suggestions)

# Test 36: Sugerencias para transformation con MongoDB
current = {"storage": "MongoDB"}
suggestions = StackValidator.suggest_compatible_options(current, "transformation")
test("MongoDB sugiere solo Spark (no dbt)", "Spark" in suggestions and "dbt" not in suggestions)

# Test 37: Sugerencias para quality con MongoDB
current = {"storage": "MongoDB"}
suggestions = StackValidator.suggest_compatible_options(current, "quality")
test("MongoDB sugiere Soda (no Great Expectations)", 
     "Soda" in suggestions and "Great Expectations" not in suggestions)

print("\n" + "=" * 80)
print("📊 RESUMEN DE TESTS")
print("=" * 80)

print(f"\nTotal de tests ejecutados: {total_tests}")
print(f"✅ Tests pasados: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
print(f"❌ Tests fallados: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")

if failed_tests == 0:
    print("\n🎉 ¡TODOS LOS TESTS PASARON! El sistema está correctamente orquestado.")
    exit_code = 0
else:
    print(f"\n⚠️  {failed_tests} test(s) fallaron. Revisar logs arriba.")
    exit_code = 1

print("=" * 80)
sys.exit(exit_code)
