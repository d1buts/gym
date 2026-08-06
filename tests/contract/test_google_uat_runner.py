from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from pathlib import Path
from types import SimpleNamespace

RUNNER_PATH = Path("scripts/run_google_uat.py")


def _runner():
    spec = importlib.util.spec_from_file_location(
        "_workout_google_uat_runner",
        RUNNER_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_google_uat_runner_exists() -> None:
    assert RUNNER_PATH.is_file(), "fail-closed Google UAT runner is missing"


@dataclass
class _Gate:
    source_alias: str = "disposable_test"
    desired_locale: str = "uk_UA"
    desired_time_zone: str = "America/New_York"

    def validate_local(self, *, require_apply: bool) -> None:
        assert require_apply is True
        if (
            self.desired_locale != "uk_UA"
            or self.desired_time_zone != "America/New_York"
        ):
            from workout_tracker.adapters.google_sheets import (
                GoogleSheetsGatewayError,
            )

            raise GoogleSheetsGatewayError(
                "DESIRED_WORKBOOK_PROPERTIES_INVALID"
            )


class _Gateway:
    def __init__(self, observed: object) -> None:
        self.observed = observed
        self.calls = 0

    def observe(self) -> object:
        self.calls += 1
        return self.observed


def _pytest_result(
    reports: list[SimpleNamespace],
    *,
    exit_code: int,
):
    def run(arguments: list[str], *, plugins: list[object]) -> int:
        assert arguments == [
            "-q",
            "--tb=no",
            "-m",
            "google_uat",
            "tests/uat/test_clean_workbook.py",
            "tests/uat/test_formula_results.py",
            "tests/uat/test_second_run.py",
        ]
        counter = plugins[0]
        for report in reports:
            counter.pytest_runtest_logreport(report)
        return exit_code

    return run


def _report(
    nodeid: str,
    *,
    when: str = "call",
    skipped: bool = False,
) -> SimpleNamespace:
    return SimpleNamespace(
        nodeid=nodeid,
        when=when,
        skipped=skipped,
        keywords={"google_uat": True},
    )


def _invoke(
    capsys,
    *,
    reports: list[SimpleNamespace],
    exit_code: int = 0,
    gate: _Gate | None = None,
    observed: object | None = None,
) -> tuple[int, str, _Gateway]:
    run_google_uat = _runner().run_google_uat

    gateway = _Gateway(
        observed
        if observed is not None
        else SimpleNamespace(locale="uk_UA", time_zone="America/New_York")
    )
    status = run_google_uat(
        environment={"WORKOUT_GOOGLE_UAT_OPT_IN": "1"},
        preflight_factory=lambda *, explicit_apply: gate or _Gate(),
        gateway_factory=lambda _: gateway,
        pytest_main=_pytest_result(reports, exit_code=exit_code),
    )
    return status, capsys.readouterr().out, gateway


def test_missing_opt_in_fails_before_preflight_or_google(capsys) -> None:
    run_google_uat = _runner().run_google_uat

    called = False

    def forbidden(*, explicit_apply: bool):
        nonlocal called
        called = True
        raise AssertionError("preflight must not run")

    status = run_google_uat(environment={}, preflight_factory=forbidden)

    output = capsys.readouterr().out
    assert status != 0
    assert called is False
    assert '"error_code": "GOOGLE_UAT_OPT_IN_REQUIRED"' in output
    assert '"google_uat_executed_count": 0' in output


def test_all_skipped_and_collection_error_cannot_pass(capsys) -> None:
    skipped_status, skipped_output, _ = _invoke(
        capsys,
        reports=[_report("private-case", when="setup", skipped=True)],
    )
    collection_status, collection_output, _ = _invoke(
        capsys,
        reports=[],
        exit_code=2,
    )

    assert skipped_status != 0
    assert '"error_code": "GOOGLE_UAT_ZERO_EXECUTED"' in skipped_output
    assert '"google_uat_executed_count": 0' in skipped_output
    assert collection_status != 0
    assert '"error_code": "GOOGLE_UAT_TESTS_FAILED"' in collection_output
    assert '"google_uat_executed_count": 0' in collection_output


def test_one_pass_is_counted_once_and_one_failure_stays_failed(capsys) -> None:
    passing = _report("private-pass")
    pass_status, pass_output, _ = _invoke(
        capsys,
        reports=[
            _report("private-pass", when="setup"),
            passing,
            _report("private-pass", when="teardown"),
            passing,
        ],
    )
    fail_status, fail_output, _ = _invoke(
        capsys,
        reports=[_report("private-fail")],
        exit_code=1,
    )

    assert pass_status == 0
    assert '"google_uat_executed_count": 1' in pass_output
    assert '"status": "pass"' in pass_output
    assert "private-pass" not in pass_output
    assert fail_status != 0
    assert '"google_uat_executed_count": 1' in fail_output
    assert '"status": "fail"' in fail_output
    assert "private-fail" not in fail_output


def test_clean_target_property_mismatch_is_managed_drift(capsys) -> None:
    observed = SimpleNamespace(locale="en_US", time_zone="Etc/UTC")
    status, output, gateway = _invoke(
        capsys,
        reports=[_report("private-clean-target")],
        observed=observed,
    )

    assert status == 0
    assert gateway.calls == 1
    assert '"status": "pass"' in output
    assert "en_US" not in output
    assert "Etc/UTC" not in output


def test_invalid_desired_properties_fail_locally_without_google(capsys) -> None:
    status, output, gateway = _invoke(
        capsys,
        reports=[],
        gate=_Gate(desired_locale="host-default"),
    )

    assert status != 0
    assert gateway.calls == 0
    assert (
        '"error_code": "DESIRED_WORKBOOK_PROPERTIES_INVALID"' in output
    )


def test_terminal_evidence_does_not_relay_pytest_or_sensitive_values(
    capsys,
) -> None:
    sensitive = "token spreadsheet-id credential-path raw-provider-error"

    def noisy_pytest(arguments: list[str], *, plugins: list[object]) -> int:
        print(sensitive)
        plugins[0].pytest_runtest_logreport(_report("secret-node-id"))
        return 1

    run_google_uat = _runner().run_google_uat

    status = run_google_uat(
        environment={"WORKOUT_GOOGLE_UAT_OPT_IN": "1"},
        preflight_factory=lambda *, explicit_apply: _Gate(),
        gateway_factory=lambda _: _Gateway(object()),
        pytest_main=noisy_pytest,
    )
    output = capsys.readouterr().out

    assert status != 0
    assert sensitive not in output
    assert "secret-node-id" not in output
    assert set(__import__("json").loads(output)) == {
        "source_alias",
        "google_uat_executed_count",
        "error_code",
        "status",
    }
