from typing import Dict, Type
from core.interfaces import ComponentGenerator

class ProviderRegistry:
    _registry: Dict[str, Dict[str, Type[ComponentGenerator]]] = {
        "ingestion": {},
        "storage": {},
        "transformation": {},
        "orchestration": {},
        "infrastructure": {},
        "visualization": {},      # NEW: Phase 3
        "quality": {},             # NEW: Phase 3
        "monitoring": {}           # NEW: Phase 3
    }
    
    @classmethod
    def register(cls, category: str, name: str, provider_cls: Type[ComponentGenerator]):
        if category not in cls._registry:
            raise ValueError(f"Invalid category: {category}")
        cls._registry[category][name] = provider_cls
        
    @classmethod
    def get_provider(cls, category: str, name: str) -> Type[ComponentGenerator]:
        if category not in cls._registry:
            raise ValueError(f"Invalid category: {category}")
        
        provider = cls._registry[category].get(name)
        if not provider:
            raise ValueError(f"Provider '{name}' not found for category '{category}'")
            
        return provider

    @classmethod
    def get_all_providers(cls) -> Dict[str, list]:
        """
        Returns a dictionary of all registered providers, categorized.
        Structure: { "ingestion": ["ToolA", "ToolB"], "storage": [...] }
        """
        return {
            category: list(tools.keys())
            for category, tools in cls._registry.items()
        }
