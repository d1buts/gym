from __future__ import annotations

import re
import tomllib
from pathlib import Path


PROJECT_ROOT = Path(__file__).parents[2]
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"

EXPECTED_RUNTIME_DEPENDENCIES = {
    "google-api-python-client",
    "google-auth",
    "pydantic",
    "pyyaml",
}
EXPECTED_DEVELOPMENT_DEPENDENCIES = {"pytest"}
EXPECTED_SOURCES = {
    "google-api-python-client": (
        "https://github.com/googleapis/google-api-python-client"
    ),
    "google-auth": (
        "https://github.com/googleapis/google-cloud-python/"
        "tree/main/packages/google-auth"
    ),
    "pydantic": "https://github.com/pydantic/pydantic",
    "pytest": "https://github.com/pytest-dev/pytest",
    "pyyaml": "https://github.com/yaml/pyyaml",
}


def _normalized_name(requirement: str) -> str:
    match = re.match(r"[A-Za-z0-9][A-Za-z0-9._-]*", requirement)
    assert match is not None, f"invalid direct dependency declaration: {requirement!r}"
    return re.sub(r"[-_.]+", "-", match.group(0)).lower()


def test_dependency_policy_matches_approved_d20_set_and_sources() -> None:
    with PYPROJECT_PATH.open("rb") as pyproject_file:
        pyproject = tomllib.load(pyproject_file)

    runtime_dependencies = {
        _normalized_name(requirement)
        for requirement in pyproject["project"]["dependencies"]
    }
    development_dependencies = {
        _normalized_name(requirement)
        for requirement in pyproject.get("dependency-groups", {}).get("dev", [])
    }

    assert runtime_dependencies == EXPECTED_RUNTIME_DEPENDENCIES
    assert development_dependencies == EXPECTED_DEVELOPMENT_DEPENDENCIES

    policy = (
        pyproject.get("tool", {})
        .get("workout_tracker", {})
        .get("dependency_policy", {})
    )
    assert policy.get("approval") == "D-20"
    assert policy.get("registry") == "https://pypi.org"
    assert policy.get("sources") == EXPECTED_SOURCES
