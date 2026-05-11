from __future__ import annotations

from typing import Type

from .base import StateResultsAdapter

_REGISTRY: dict[str, Type[StateResultsAdapter]] = {}


def register(adapter_class: Type[StateResultsAdapter]) -> Type[StateResultsAdapter]:
    """Decorator to register an adapter by its state attribute."""
    _REGISTRY[adapter_class.state.upper()] = adapter_class
    return adapter_class


def get_adapter(state: str) -> Type[StateResultsAdapter] | None:
    return _REGISTRY.get(state.upper())


def list_supported_states() -> list[str]:
    return sorted(_REGISTRY.keys())
