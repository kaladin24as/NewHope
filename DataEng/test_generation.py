"""Test de generación de proyectos completos"""
import sys
import os
import shutil
sys.path.insert(0, "backend")

from core.engine import TemplateEngine
from core.registry import ProviderRegistry

print("="*80)
print("🏭 TESTS DE GENERACIÓN DE PROYECTOS")
print("="*80)

# Test stacks
test_stacks = [
    {
        "name": "Modern_Data_Stack",
        "stack": {
            "ingestion": "DLT",
            "storage": "PostgreSQL",
            "transformation": "dbt",
            "orchestration": "Airflow"
        }
    },
    {
        "name": "Enterprise_Cloud",
        "stack": {
            "ingestion": "Airbyte",
            "storage": "Snowflake",
            "transformation": "dbt",
            "orchestration": "Airflow",
            "infrastructure": "Terraform",
            "visualization": "Superset"
        }
    },
    {
        "name": "Streaming_Stack",
        "stack": {
            "ingestion": "Kafka",
            "storage": "PostgreSQL",
            "transformation": "Spark",
            "orchestration": "Airflow"
        }
    },
    {
        "name": "NoSQL_Stack",
        "stack": {
            "storage": "MongoDB",
            "transformation": "Spark",
            "quality": "Soda"
        }
    },
    {
        "name": "Development_Stack",
        "stack": {
            "storage": "DuckDB",
            "transformation": "dbt"
        }
    }
]

engine = TemplateEngine()
passed = 0
failed = 0

for test_config in test_stacks:
    test_name = test_config["name"]
    stack = test_config["stack"]
    
    try:
        print(f"\n📝 Generando: {test_name}")
        print(f"   Stack: {stack}")
        
        vfs = engine.generate(test_name, stack, f"test-{test_name}")
        
        files = vfs.list_files()
        print(f"   ✅ Generado: {len(files)} archivos")
        
        # Verificar archivos clave
        required_files = ["README.md", "docker-compose.yml", ".gitignore"]
        for req_file in required_files:
            if req_file in files:
                print(f"      ✓ {req_file}")
            else:
                print(f"      ✗ {req_file} FALTANTE")
        
        # Verificar que hay .env files
        env_files = [f for f in files if ".env" in f]
        print(f"      ✓ {len(env_files)} archivos .env")
        
        # Verificar ARCHITECTURE.md
        if "ARCHITECTURE.md" in files:
            print(f"      ✓ ARCHITECTURE.md")
        
        passed += 1
        print(f"   ✅ {test_name}: ÉXITO")
        
    except Exception as e:
        failed += 1
        print(f"   ❌ {test_name}: ERROR - {e}")

print("\n" + "="*80)
print(f"📊 RESULTADOS:")
print(f"   ✅ Proyectos generados exitosos: {passed}/{len(test_stacks)}")
print(f"   ❌ Proyectos fallidos: {failed}/{len(test_stacks)}")

if failed == 0:
    print("\n🎉 ¡TODOS LOS PROYECTOS SE GENERARON CORRECTAMENTE!")
else:
    print(f"\n⚠️  {failed} proyecto(s) fallaron")

print("="*80)
