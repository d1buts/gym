from pathlib import Path


RUNNER_PATH = Path("scripts/run_google_uat.py")


def test_google_uat_runner_exists() -> None:
    assert RUNNER_PATH.is_file(), "fail-closed Google UAT runner is missing"
