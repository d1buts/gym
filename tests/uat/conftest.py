from __future__ import annotations

from typing import Protocol


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


__all__ = ["GoogleUATExecutionCounter"]
