from __future__ import annotations

from pathlib import Path


class ContractValidationError(ValueError):
    pass


class SourceSchema:
    pass


def load_source_schema(path: str | Path) -> SourceSchema | None:
    return None
