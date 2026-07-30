from __future__ import annotations

from pathlib import Path

from workout_tracker.contracts.source_schema import SourceSchema


class ManagedObjectBlueprint:
    pass


class TabBlueprint:
    pass


class WorkbookBlueprint:
    pass


def load_workbook_blueprint(
    path: str | Path,
    source_schema: SourceSchema,
) -> WorkbookBlueprint | None:
    return None
