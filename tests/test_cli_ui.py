"""Tests for cli/ui.py shared Console, main --version/--quiet, and run_with_spinner quiet param."""
import sys
from unittest.mock import patch

import pytest
from click.testing import CliRunner
from rich.console import Console


# ---------------------------------------------------------------------------
# Test 1: console import
# ---------------------------------------------------------------------------

def test_console_import():
    """from meeting_notes.cli.ui import console succeeds and is a Rich Console instance."""
    from meeting_notes.cli.ui import console
    assert isinstance(console, Console)


# ---------------------------------------------------------------------------
# Test 2: TTY detection
# ---------------------------------------------------------------------------

def test_console_not_terminal_when_not_tty():
    """When sys.stdout.isatty() returns False, console.is_terminal is False."""
    # Force a module reload with isatty patched
    import importlib
    with patch("sys.stdout") as mock_stdout:
        mock_stdout.isatty.return_value = False
        # Reload to pick up the patched isatty
        import meeting_notes.cli.ui as ui_module
        importlib.reload(ui_module)
        assert ui_module.console.is_terminal is False or not ui_module.console.is_terminal


# ---------------------------------------------------------------------------
# Test 3: --version flag
# ---------------------------------------------------------------------------

def test_main_version_flag():
    """Invoking `main --version` prints version and exits 0."""
    from meeting_notes.cli.main import main
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    # Should contain version info
    assert "0.1.0" in result.output or "version" in result.output.lower()


# ---------------------------------------------------------------------------
# Test 4: --quiet flag sets ctx.obj["quiet"] = True
# ---------------------------------------------------------------------------

def test_main_quiet_sets_context():
    """Invoking `main --quiet record` sets ctx.obj['quiet'] to True."""
    from meeting_notes.cli.main import main
    import click

    captured_quiet = {}

    @main.command("test-quiet")
    @click.pass_context
    def test_quiet_cmd(ctx):
        captured_quiet["quiet"] = ctx.obj.get("quiet", "NOT_SET")

    runner = CliRunner()
    result = runner.invoke(main, ["--quiet", "test-quiet"])
    assert result.exit_code == 0
    assert captured_quiet.get("quiet") is True

    # Cleanup: remove the test command
    main.commands.pop("test-quiet", None)


# ---------------------------------------------------------------------------
# Test 5: run_with_spinner quiet=True calls fn() directly (no thread)
# ---------------------------------------------------------------------------

def test_run_with_spinner_quiet_true():
    """run_with_spinner(fn, msg, quiet=True) calls fn() directly and returns result."""
    from meeting_notes.services.transcription import run_with_spinner

    called = {"count": 0}

    def fn():
        called["count"] += 1
        return "result_value"

    result = run_with_spinner(fn, "test message", quiet=True)
    assert result == "result_value"
    assert called["count"] == 1


# ---------------------------------------------------------------------------
# Test 6: run_with_spinner quiet=False uses threaded spinner (existing behavior)
# ---------------------------------------------------------------------------

def test_run_with_spinner_quiet_false():
    """run_with_spinner(fn, msg, quiet=False) runs normally and returns result."""
    from meeting_notes.services.transcription import run_with_spinner
    import threading

    thread_names = []

    def fn():
        # Capture that we are NOT on the main thread when quiet=False
        thread_names.append(threading.current_thread().name)
        return 42

    result = run_with_spinner(fn, "test message", quiet=False)
    assert result == 42
    # When not quiet, fn runs in a background thread (not main thread)
    assert any(name != "MainThread" for name in thread_names)
