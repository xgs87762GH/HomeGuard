"""
Provider Auto-Discovery System
Automatically finds and loads all Provider subclasses with zero configuration
"""

import importlib.util
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Type

try:
    from .base_provider import BaseProvider
    from ..core.config.setting import LOGGER
except ImportError:
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from src.providers.base_provider import BaseProvider
    from src.core.config.setting import LOGGER


class ProviderLoader:
    """Elegant Provider auto-discovery and loading"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.providers: Dict[str, BaseProvider] = {}

    def load_all(self) -> List[BaseProvider]:
        """Main entry point - discovers and loads all providers"""
        self._auto_import_providers()
        provider_classes = self._discover_provider_classes()
        return self._instantiate_providers(provider_classes)

    def _auto_import_providers(self):
        """Smart import of provider modules"""
        for provider_file in self._find_provider_files():
            self._safe_import(provider_file)

    def _find_provider_files(self) -> List[Path]:
        """Find files that likely contain providers"""
        providers_dir = Path(__file__).parent
        candidates = []

        for py_file in providers_dir.rglob("*.py"):
            if self._is_provider_file(py_file):
                candidates.append(py_file)

        return candidates

    def _is_provider_file(self, py_file: Path) -> bool:
        """Check if file contains a provider class"""
        # Skip obvious non-provider files
        if (py_file.name.startswith("__") or
            py_file.name == "base_provider.py" or
            "test" in py_file.name):
            return False

        # Provider files usually end with _provider.py or contain BaseProvider
        if py_file.name.endswith("_provider.py"):
            return True

        return self._contains_provider_class(py_file)

    def _contains_provider_class(self, py_file: Path) -> bool:
        """Quick check if file defines a Provider class"""
        try:
            content = py_file.read_text(encoding='utf-8')
            return "BaseProvider" in content and "class " in content
        except Exception:
            return False

    def _safe_import(self, py_file: Path):
        """Import module without breaking the loading process"""
        try:
            module_name = self._build_module_name(py_file)
            if module_name in sys.modules:
                return

            spec = importlib.util.spec_from_file_location(module_name, py_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)

        except Exception as e:
            LOGGER.debug(f"Could not import {py_file.name}: {e}")

    def _build_module_name(self, py_file: Path) -> str:
        """Convert file path to module name"""
        providers_dir = Path(__file__).parent
        relative_path = py_file.relative_to(providers_dir.parent)
        return ".".join(relative_path.with_suffix("").parts)

    def _discover_provider_classes(self) -> Dict[str, Type[BaseProvider]]:
        """Find all registered Provider subclasses"""
        providers = {}

        for provider_class in self._get_all_subclasses(BaseProvider):
            if self._is_valid_provider(provider_class):
                providers[provider_class.__name__] = provider_class

        return providers

    def _get_all_subclasses(self, cls) -> set:
        """Recursively get all subclasses"""
        subclasses = set(cls.__subclasses__())
        for subclass in list(subclasses):
            subclasses.update(self._get_all_subclasses(subclass))
        return subclasses

    def _is_valid_provider(self, provider_class: Type[BaseProvider]) -> bool:
        """Check if provider class should be loaded"""
        return not (
            # Skip abstract classes
            hasattr(provider_class, '__abstractmethods__') and provider_class.__abstractmethods__ or
            # Skip test classes
            'test' in provider_class.__module__.lower()
        )

    def _instantiate_providers(self, provider_classes: Dict[str, Type[BaseProvider]]) -> List[BaseProvider]:
        """Create instances of all valid providers"""
        providers = []

        for class_name, provider_class in provider_classes.items():
            try:
                config = self._get_config_for(provider_class)

                if not config.get("enabled", True):
                    continue

                instance = self._create_instance(provider_class, config)
                if instance and not self._has_name_conflict(instance):
                    self.providers[instance.name] = instance
                    providers.append(instance)
                    LOGGER.info(f"Loaded: {instance.name}")

            except Exception as e:
                LOGGER.error(f"Failed to load {class_name}: {e}")

        return providers

    def _get_config_for(self, provider_class: Type[BaseProvider]) -> Dict[str, Any]:
        """Get configuration for a provider class"""
        name = provider_class.__name__.lower().replace("provider", "")

        return (
            self.config.get("providers", {}).get(name) or
            self.config.get(name) or
            {"enabled": True}
        )

    def _create_instance(self, provider_class: Type[BaseProvider], config: Dict[str, Any]) -> Optional[BaseProvider]:
        """Create provider instance with appropriate config"""
        import inspect

        sig = inspect.signature(provider_class.__init__)
        params = list(sig.parameters.keys())[1:]  # Exclude self

        if not params:
            return provider_class()
        elif "config" in params:
            return provider_class(config=config)
        else:
            kwargs = {param: config.get(param) for param in params if param in config}
            return provider_class(**kwargs)

    def _has_name_conflict(self, instance: BaseProvider) -> bool:
        """Check for provider name conflicts"""
        if instance.name in self.providers:
            LOGGER.warning(f"Name conflict: {instance.name}")
            return True
        return False

    def get_provider(self, name: str) -> Optional[BaseProvider]:
        """Get provider by name"""
        return self.providers.get(name)

    def get_all_providers(self) -> List[BaseProvider]:
        """Get all loaded providers"""
        return list(self.providers.values())


# Global loader instance
_loader: Optional[ProviderLoader] = None


def initialize_providers(config: Optional[Dict[str, Any]] = None) -> List[BaseProvider]:
    """Initialize and return all providers"""
    global _loader
    _loader = ProviderLoader(config)
    return _loader.load_all()


def get_all_providers() -> List[BaseProvider]:
    """Get all providers (auto-initialize if needed)"""
    if _loader is None:
        initialize_providers()
    return _loader.get_all_providers()


def get_provider(name: str) -> Optional[BaseProvider]:
    """Get specific provider by name"""
    if _loader is None:
        initialize_providers()
    return _loader.get_provider(name)


# Backward compatibility
def get_all_adapters() -> List[BaseProvider]:
    """Deprecated: use get_all_providers()"""
    return get_all_providers()


def _test():
    """Quick test"""
    config = {"providers": {"camera": {"enabled": True}}}

    providers = initialize_providers(config)
    print(f"🎉 Auto-loaded {len(providers)} providers:")
    for p in providers:
        print(f"  ✓ {p.name}")


if __name__ == '__main__':
    _test()