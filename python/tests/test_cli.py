"""Tests for the ``manabi`` command-line interface."""

import json

from typer.testing import CliRunner

from manabi_forge import __version__
from manabi_forge.cli.main import EXIT_MISSING_DEPENDENCY, EXIT_OK, app

runner = CliRunner()


def test_version_command():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == EXIT_OK
    assert result.output.strip() == __version__


def test_doctor_human_readable_output():
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code in (EXIT_OK, EXIT_MISSING_DEPENDENCY)
    assert "python" in result.output


def test_doctor_json_output():
    result = runner.invoke(app, ["doctor", "--json"])
    assert result.exit_code in (EXIT_OK, EXIT_MISSING_DEPENDENCY)
    payload = json.loads(result.output)
    first = payload["checks"][0]
    assert {"name", "required", "ok", "detail", "hint"} <= set(first)
