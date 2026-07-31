from __future__ import annotations

import importlib.util
import io
import json
import os
import sys
from collections.abc import Callable, Mapping, Sequence
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Protocol

import pytest

_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_SOURCE_ROOT = _REPOSITORY_ROOT / "src"
if str(_SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(_SOURCE_ROOT))

from workout_tracker.adapters.google_sheets import (
    GoogleSheetsGateway,
    GoogleSheetsGatewayError,
    GoogleUATPreflight,
)


GOOGLE_UAT_OPT_IN = "WORKOUT_GOOGLE_UAT_OPT_IN"
UAT_MODULES = (
    "tests/uat/test_clean_workbook.py",
    "tests/uat/test_formula_results.py",
    "tests/uat/test_second_run.py",
)


class _Counter(Protocol):
    executed_count: int


class _PreflightFactory(Protocol):
    def __call__(self, *, explicit_apply: bool) -> GoogleUATPreflight: ...


def _load_counter() -> _Counter:
    path = Path("tests/uat/conftest.py")
    spec = importlib.util.spec_from_file_location(
        "_workout_google_uat_counter",
        path,
    )
    if spec is None or spec.loader is None:
        raise GoogleSheetsGatewayError("UAT_COUNTER_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    counter_type = getattr(module, "GoogleUATExecutionCounter", None)
    if counter_type is None:
        raise GoogleSheetsGatewayError("UAT_COUNTER_UNAVAILABLE")
    return counter_type()


def _emit(evidence: Mapping[str, object]) -> None:
    print(json.dumps(dict(evidence), sort_keys=True))


def run_google_uat(
    *,
    environment: Mapping[str, str] | None = None,
    preflight_factory: _PreflightFactory = GoogleUATPreflight.from_environment,
    gateway_factory: Callable[[GoogleUATPreflight], object] = GoogleSheetsGateway,
    pytest_main: Callable[..., int | pytest.ExitCode] = pytest.main,
    counter_factory: Callable[[], _Counter] = _load_counter,
) -> int:
    values = os.environ if environment is None else environment
    source_alias: str | None = None
    counter: _Counter | None = None
    try:
        if values.get(GOOGLE_UAT_OPT_IN) != "1":
            raise GoogleSheetsGatewayError("GOOGLE_UAT_OPT_IN_REQUIRED")

        gate = preflight_factory(explicit_apply=True)
        source_alias = gate.source_alias
        gate.validate_local(require_apply=True)

        gateway = gateway_factory(gate)
        gateway.observe()  # type: ignore[attr-defined]

        counter = counter_factory()
        arguments: Sequence[str] = (
            "-q",
            "--tb=no",
            "-m",
            "google_uat",
            *UAT_MODULES,
        )
        captured = io.StringIO()
        with redirect_stdout(captured), redirect_stderr(captured):
            pytest_status = int(pytest_main(list(arguments), plugins=[counter]))

        executed = counter.executed_count
        if pytest_status != 0:
            raise GoogleSheetsGatewayError("GOOGLE_UAT_TESTS_FAILED")
        if executed == 0:
            raise GoogleSheetsGatewayError("GOOGLE_UAT_ZERO_EXECUTED")

        _emit(
            {
                "source_alias": source_alias,
                "google_uat_executed_count": executed,
                "status": "pass",
            }
        )
        return 0
    except Exception as exc:
        code = getattr(exc, "code", "GOOGLE_UAT_FAILED")
        evidence: dict[str, object] = {
            "google_uat_executed_count": (
                counter.executed_count if counter is not None else 0
            ),
            "error_code": code,
            "status": "fail",
        }
        if source_alias is not None:
            evidence["source_alias"] = source_alias
        _emit(evidence)
        return 2


def main() -> int:
    return run_google_uat()


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["GOOGLE_UAT_OPT_IN", "UAT_MODULES", "main", "run_google_uat"]
