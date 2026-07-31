from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import pytest
import yaml

from workout_tracker.adapters.google_sheets import (
    GoogleSheetsGateway,
    GoogleUATPreflight,
)
from workout_tracker.adapters.port import (
    ApplyResult,
    ChangePlan,
    ObservedWorkbook,
)
from workout_tracker.contracts import (
    load_program_bootstrap,
    load_source_schema,
    load_workbook_blueprint,
)
from workout_tracker.workbook import compile_desired_workbook
from workout_tracker.workbook.model import DesiredWorkbook
from workout_tracker.workbook.reconcile import plan_setup


GOOGLE_UAT_OPT_IN = "WORKOUT_GOOGLE_UAT_OPT_IN"


def google_uat_enabled(environment: Mapping[str, str] | None = None) -> bool:
    values = os.environ if environment is None else environment
    return values.get(GOOGLE_UAT_OPT_IN) == "1"


class _CallReport(Protocol):
    when: str
    skipped: bool
    nodeid: str
    keywords: dict[str, object]


class GoogleUATExecutionCounter:
    """Count marked tests whose call phase ran, without retaining node IDs."""

    def __init__(self) -> None:
        self._executed_nodeids: set[str] = set()

    @property
    def executed_count(self) -> int:
        return len(self._executed_nodeids)

    def pytest_runtest_logreport(self, report: _CallReport) -> None:
        if (
            report.when == "call"
            and not report.skipped
            and "google_uat" in report.keywords
        ):
            self._executed_nodeids.add(report.nodeid)


@dataclass(slots=True)
class GoogleUATSession:
    desired: DesiredWorkbook
    gateway: GoogleSheetsGateway
    initial: ObservedWorkbook
    first_plan: ChangePlan | None = None
    first_result: ApplyResult | None = None
    first_observed: ObservedWorkbook | None = None

    def initialize(self) -> ObservedWorkbook:
        if self.first_observed is None:
            self.first_plan = plan_setup(self.desired, self.initial)
            self.first_result = self.gateway.apply(self.first_plan)
            self.first_observed = self.gateway.observe()
        return self.first_observed


def _desired_workbook() -> DesiredWorkbook:
    schema = load_source_schema(Path("config/schema.yaml"))
    blueprint = load_workbook_blueprint(
        Path("config/workbook-blueprint.yaml"),
        schema,
    )
    program = load_program_bootstrap(
        Path("config/program-bootstrap.yaml"),
        schema,
    )
    return compile_desired_workbook(
        blueprint,
        schema,
        program,
        locale="uk_UA",
        time_zone="America/New_York",
    )


@pytest.fixture(scope="session")
def google_uat_session() -> GoogleUATSession:
    gate = GoogleUATPreflight.from_environment(explicit_apply=True)
    gate.validate_local(require_apply=True)
    gateway = GoogleSheetsGateway(gate)
    return GoogleUATSession(
        desired=_desired_workbook(),
        gateway=gateway,
        initial=gateway.observe(),
    )


@pytest.fixture(scope="session")
def canonical_metric_cases() -> tuple[dict[str, object], ...]:
    payload = yaml.safe_load(
        Path("tests/fixtures/metrics-v1.yaml").read_text(encoding="utf-8")
    )
    assert payload["formula_version"] == "metrics-v1"
    return tuple(payload["cases"])


__all__ = [
    "GoogleUATExecutionCounter",
    "GoogleUATSession",
    "canonical_metric_cases",
    "google_uat_enabled",
    "google_uat_session",
]
