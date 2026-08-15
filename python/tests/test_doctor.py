"""Tests for manabi_forge.doctor."""

from manabi_forge.doctor import CheckResult, DoctorReport, run_checks


def test_run_checks_includes_python_and_git():
    report = run_checks()
    names = [check.name for check in report.checks]
    assert "python" in names
    assert "git" in names


def test_python_check_passes_on_current_interpreter():
    report = run_checks()
    python_check = next(check for check in report.checks if check.name == "python")
    assert python_check.ok
    assert python_check.required


def test_report_ok_ignores_optional_failures():
    report = DoctorReport(
        checks=[
            CheckResult(name="git", required=True, ok=True, detail="/usr/bin/git"),
            CheckResult(name="latexmk", required=False, ok=False, detail="not found"),
        ],
    )
    assert report.ok


def test_report_not_ok_when_required_check_fails():
    report = DoctorReport(
        checks=[
            CheckResult(name="git", required=True, ok=False, detail="not found"),
        ],
    )
    assert not report.ok
