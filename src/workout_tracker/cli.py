from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Sequence

from workout_tracker.adapters.memory import InMemoryWorkbookGateway
from workout_tracker.contracts import (
    load_program_bootstrap,
    load_source_schema,
    load_workbook_blueprint,
)
from workout_tracker.workbook import compile_desired_workbook
from workout_tracker.workbook.reconcile import plan_setup


_SCHEMA = Path("config/schema.yaml")
_BLUEPRINT = Path("config/workbook-blueprint.yaml")
_PROGRAM = Path("config/program-bootstrap.yaml")


def _desired():
    schema = load_source_schema(_SCHEMA)
    blueprint = load_workbook_blueprint(_BLUEPRINT, schema)
    program = load_program_bootstrap(_PROGRAM, schema)
    return compile_desired_workbook(
        blueprint,
        schema,
        program,
        locale="uk_UA",
        time_zone="America/New_York",
    )


def _safe_summary(plan, *, status: str) -> dict[str, object]:
    kinds = Counter(
        getattr(operation, "kind", type(operation).__name__)
        for operation in plan.operations
    )
    desired = _desired()
    return {
        "status": status,
        "workbook_contract_version": desired.workbook_contract_version,
        "schema_version": desired.schema_version,
        "formula_version": desired.formula_version,
        "expected_fingerprint": plan.expected_fingerprint,
        "operation_count": len(plan.operations),
        "operation_kinds": dict(sorted(kinds.items())),
    }


def _offline_plan():
    gateway = InMemoryWorkbookGateway()
    return plan_setup(_desired(), gateway.observe()), gateway


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="workout-tracker")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("validate")
    subcommands.add_parser("memory-dry-run")
    subcommands.add_parser("memory-apply")
    subcommands.add_parser("google-dry-run")
    live = subcommands.add_parser("google-apply")
    live.add_argument("--apply", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "validate":
            desired = _desired()
            output = {
                "status": "valid",
                "workbook_contract_version": desired.workbook_contract_version,
                "schema_version": desired.schema_version,
                "formula_version": desired.formula_version,
            }
        elif args.command in {"memory-dry-run", "google-dry-run"}:
            plan, _ = _offline_plan()
            output = _safe_summary(plan, status="dry_run")
        elif args.command == "memory-apply":
            plan, gateway = _offline_plan()
            result = gateway.apply(plan)
            output = {
                **_safe_summary(plan, status=result.status),
                "after_fingerprint": result.after_fingerprint,
            }
        else:
            from workout_tracker.adapters.google_sheets import (
                GoogleSheetsGateway,
                GoogleSheetsGatewayError,
                GoogleUATPreflight,
            )

            gate = GoogleUATPreflight.from_environment(
                explicit_apply=bool(args.apply)
            )
            gateway = GoogleSheetsGateway(gate)
            observed = gateway.observe()
            plan = plan_setup(_desired(), observed)
            result = gateway.apply(plan)
            output = {
                **_safe_summary(plan, status=result.status),
                "source_alias": gate.source_alias,
                "after_fingerprint": result.after_fingerprint,
            }
    except Exception as exc:
        code = getattr(exc, "code", "COMMAND_FAILED")
        print(json.dumps({"status": "error", "code": code}, sort_keys=True))
        return 2
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["main"]
