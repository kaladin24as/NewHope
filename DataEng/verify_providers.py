import sys
sys.path.insert(0, 'backend')

from core.providers import *
from core.registry import ProviderRegistry

providers = ProviderRegistry.get_all_providers()

print(f"\n{'='*60}")
print("ANTIGRAVITY - REGISTERED PROVIDERS")
print(f"{'='*60}\n")

total = 0
for category, provider_list in sorted(providers.items()):
    print(f"{category.upper():<20} ({len(provider_list)} providers)")
    for provider in sorted(provider_list):
        print(f"  ✓ {provider}")
    print()
    total += len(provider_list)

print(f"{'='*60}")
print(f"TOTAL: {total} providers registered")
print(f"{'='*60}")
