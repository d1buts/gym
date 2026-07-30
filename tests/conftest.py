from __future__ import annotations

import os
from collections.abc import Mapping

import pytest


GOOGLE_UAT_OPT_IN = "WORKOUT_GOOGLE_UAT_OPT_IN"


def google_uat_enabled(environment: Mapping[str, str] | None = None) -> bool:
    """Return whether the dedicated live runner explicitly enabled Google UAT."""
    values = os.environ if environment is None else environment
    return values.get(GOOGLE_UAT_OPT_IN) == "1"


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Keep ordinary collection and execution credential-free and offline."""
    if google_uat_enabled():
        return

    offline_skip = pytest.mark.skip(
        reason="google_uat requires the dedicated, preflighted live runner"
    )
    for item in items:
        if "google_uat" in item.keywords:
            item.add_marker(offline_skip)
