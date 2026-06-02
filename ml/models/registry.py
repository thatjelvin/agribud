"""Yield model registry.

The registry is the single source of truth for which implementation backs
``ml.inference.realtime.predict``. It satisfies the ML Development Rules
in ARCHITECTURE.md (§4) — *support versioning, retraining, replacement* —
by:

* name → class mapping (set via :func:`register` or the ``YIELD_MODEL`` env var)
* the active model is selected at import time from ``app.config.settings``
* ``list_versions()`` exposes the catalog for ops/UI surfaces
* ``get_active()`` returns an instance of the currently active model
"""

from __future__ import annotations

import importlib
from typing import Type

from ml.models.base import YieldModel
from ml.models.statistical_v1 import StatisticalYieldModelV1


_REGISTRY: dict[str, Type[YieldModel]] = {
    "v1-statistical": StatisticalYieldModelV1,
}

DEFAULT_VERSION = "v1-statistical"


def register(name: str, model_cls: Type[YieldModel]) -> None:
    """Add or replace a yield model in the registry."""
    if not issubclass(model_cls, YieldModel):
        raise TypeError(f"{model_cls!r} is not a YieldModel subclass")
    _REGISTRY[name] = model_cls


def resolve(name: str) -> Type[YieldModel]:
    """Return the registered class for ``name`` or raise ``KeyError``."""
    try:
        return _REGISTRY[name]
    except KeyError as exc:
        raise KeyError(
            f"Unknown yield model '{name}'. Known: {sorted(_REGISTRY)}"
        ) from exc


def list_versions() -> list[dict[str, str]]:
    """Catalog for ops/UI: name, module, class."""
    return [
        {
            "name": cls.version or name,
            "module": cls.__module__,
            "class": cls.__name__,
        }
        for name, cls in sorted(_REGISTRY.items())
    ]


def get_active(version: str | None = None) -> YieldModel:
    """Instantiate the active yield model.

    ``version`` wins over the env-var default. Falls back to
    :data:`DEFAULT_VERSION` if neither is registered.
    """
    name = version or DEFAULT_VERSION
    try:
        return resolve(name)()
    except KeyError:
        return _REGISTRY[DEFAULT_VERSION]()


def get_default_for_env(env_value: str | None) -> YieldModel:
    """Resolve the env-var-driven default.

    Accepts either a registered name (e.g. ``v1-statistical``) or a
    ``module:Class`` dotted path for lazy registration without a hard
    import cycle.
    """
    if not env_value:
        return get_active(DEFAULT_VERSION)
    if env_value in _REGISTRY:
        return _REGISTRY[env_value]()
    if ":" in env_value:
        module_path, class_name = env_value.split(":", 1)
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
        return cls()
    return get_active(DEFAULT_VERSION)
