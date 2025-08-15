import importlib.util
import inspect
import sys
from pathlib import Path
from typing import List

from src.adapter.base_adapter import BaseAdapter
from src.core.config.setting import LOGGER, setup_logging


def get_all_adapters() -> List[BaseAdapter]:
    """
    Scans all *.py files under src/adapter/**,
    returns instances of all BaseAdapter subclasses (lazy import, no duplicates).
    """
    base = Path(__file__).resolve().parent
    adapters: List[BaseAdapter] = []

    for py in base.rglob("*.py"):
        if py.name.startswith("__"):
            continue

        # Convert file path to Python-style module name
        # Example: E:\...\src\adapter\camera\adapter.py -> "adapter.camera.adapter"
        rel = py.relative_to(base.parent).with_suffix("")
        mod_name = ".".join(rel.parts)

        # Create module spec from file location
        spec = importlib.util.spec_from_file_location(mod_name, py)
        if not spec or not spec.loader:
            continue

        # Load the module
        mod = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = mod
        spec.loader.exec_module(mod)

        # Find and instantiate subclasses of BaseAdapter
        for name, cls in inspect.getmembers(mod, inspect.isclass):
            if issubclass(cls, BaseAdapter) and cls != BaseAdapter:
                instance = cls()
                if instance.name not in {a.name for a in adapters}:
                    adapters.append(instance)
                    LOGGER.info("Loaded adapter: %s", instance.name)

    return adapters


if __name__ == '__main__':
    setup_logging()
    print(get_all_adapters())
