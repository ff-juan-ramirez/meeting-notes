"""Tests for meet init full interactive wizard."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner
from notion_client.errors import APIResponseError

from meeting_notes.cli.commands.init import init, mask_token


# ---------------------------------------------------------------------------
# mask_token unit tests
# ---------------------------------------------------------------------------

def test_mask_token_none():
    assert mask_token(None) == "[not set]"


def test_mask_token_short():
    assert mask_token("short") == "***"


def test_mask_token_exactly_8_chars():
    assert mask_token("12345678") == "***"


def test_mask_token_normal():
    assert mask_token("ntn_abcdefghijk") == "ntn_***ijk"


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

FAKE_DEVICES = {0: "MacBook Air Microphone", 1: "BlackHole 2ch", 2: "External Mic"}
FAKE_CONFIG_DIR = "/tmp/test-meet-config"


def _fake_notion_error():
    """Create a real APIResponseError for mocking."""
    import httpx
    return APIResponseError(
        code="unauthorized",
        status=401,
        message="Invalid token",
        headers=httpx.Headers({}),
        raw_body_text='{"status": 401, "code": "unauthorized", "message": "Invalid token"}',
    )


# ---------------------------------------------------------------------------
# First-time init (no config exists) — full wizard
# ---------------------------------------------------------------------------

def test_first_time_init_runs_full_wizard(tmp_path):
    """First-time init runs full wizard: devices, Notion, config save, test recording, doctor."""
    runner = CliRunner()

    with (
        patch("meeting_notes.cli.commands.init._parse_audio_devices", return_value=FAKE_DEVICES),
        patch("meeting_notes.cli.commands.init.NotionClient") as mock_nc,
        patch("meeting_notes.cli.commands.init.subprocess.run"),
        patch("meeting_notes.cli.commands.init.HealthCheckSuite") as mock_suite_cls,
        patch("meeting_notes.cli.commands.init.get_config_dir", return_value=tmp_path),
        patch("meeting_notes.cli.commands.init.ensure_dirs"),
    ):
        mock_nc.return_value.users.me.return_value = {"id": "user-1"}
        mock_suite = MagicMock()
        mock_suite.run_all.return_value = []
        mock_suite_cls.return_value = mock_suite

        # Input: system device=1, mic device=2, token=ntn_test, page_id=page123
        result = runner.invoke(
            init,
            obj={"quiet": False},
            input="1\n2\nntn_testtoken\npage123\n",
        )

    assert result.exit_code == 0, result.output
    config_path = tmp_path / "config.json"
    assert config_path.exists(), "Config should be saved after first-time wizard"
    mock_suite.run_all.assert_called_once()


def test_first_time_init_saves_correct_config_values(tmp_path):
    """Config saved with AudioConfig and NotionConfig from wizard prompts."""
    import json
    runner = CliRunner()

    with (
        patch("meeting_notes.cli.commands.init._parse_audio_devices", return_value=FAKE_DEVICES),
        patch("meeting_notes.cli.commands.init.NotionClient") as mock_nc,
        patch("meeting_notes.cli.commands.init.subprocess.run"),
        patch("meeting_notes.cli.commands.init.HealthCheckSuite") as mock_suite_cls,
        patch("meeting_notes.cli.commands.init.get_config_dir", return_value=tmp_path),
        patch("meeting_notes.cli.commands.init.ensure_dirs"),
    ):
        mock_nc.return_value.users.me.return_value = {"id": "user-1"}
        mock_suite = MagicMock()
        mock_suite.run_all.return_value = []
        mock_suite_cls.return_value = mock_suite

        result = runner.invoke(
            init,
            obj={"quiet": False},
            input="1\n2\nntn_token_abc\npage_xyz\n",
        )

    assert result.exit_code == 0, result.output
    config_data = json.loads((tmp_path / "config.json").read_text())
    assert config_data["audio"]["system_device_index"] == 1
    assert config_data["audio"]["microphone_device_index"] == 2
    assert config_data["notion"]["token"] == "ntn_token_abc"
    assert config_data["notion"]["parent_page_id"] == "page_xyz"


def test_first_time_init_calls_test_recording(tmp_path):
    """Test recording subprocess is called with mic device index after config save."""
    runner = CliRunner()
    captured_calls = []

    def capture_run(cmd, **kwargs):
        captured_calls.append(cmd)
        return MagicMock(returncode=0)

    with (
        patch("meeting_notes.cli.commands.init._parse_audio_devices", return_value=FAKE_DEVICES),
        patch("meeting_notes.cli.commands.init.NotionClient") as mock_nc,
        patch("meeting_notes.cli.commands.init.subprocess.run", side_effect=capture_run),
        patch("meeting_notes.cli.commands.init.HealthCheckSuite") as mock_suite_cls,
        patch("meeting_notes.cli.commands.init.get_config_dir", return_value=tmp_path),
        patch("meeting_notes.cli.commands.init.ensure_dirs"),
    ):
        mock_nc.return_value.users.me.return_value = {}
        mock_suite = MagicMock()
        mock_suite.run_all.return_value = []
        mock_suite_cls.return_value = mock_suite

        result = runner.invoke(
            init,
            obj={"quiet": False},
            input="1\n2\nntn_tok\npage1\n",
        )

    assert result.exit_code == 0, result.output
    # Should have at least one subprocess.run for test recording
    assert len(captured_calls) > 0
    # The test recording call contains "-t" and "1"
    recording_calls = [c for c in captured_calls if "-t" in c and "1" in c]
    assert len(recording_calls) > 0, f"No test recording call found in: {captured_calls}"


def test_first_time_init_runs_inline_doctor(tmp_path):
    """Inline doctor uses HealthCheckSuite.run_all() (not subprocess)."""
    runner = CliRunner()

    with (
        patch("meeting_notes.cli.commands.init._parse_audio_devices", return_value=FAKE_DEVICES),
        patch("meeting_notes.cli.commands.init.NotionClient") as mock_nc,
        patch("meeting_notes.cli.commands.init.subprocess.run"),
        patch("meeting_notes.cli.commands.init.HealthCheckSuite") as mock_suite_cls,
        patch("meeting_notes.cli.commands.init.get_config_dir", return_value=tmp_path),
        patch("meeting_notes.cli.commands.init.ensure_dirs"),
    ):
        mock_nc.return_value.users.me.return_value = {}
        mock_suite = MagicMock()
        mock_suite.run_all.return_value = []
        mock_suite_cls.return_value = mock_suite

        result = runner.invoke(
            init,
            obj={"quiet": False},
            input="1\n2\nntn_tok\npage1\n",
        )

    assert result.exit_code == 0, result.output
    mock_suite_cls.assert_called_once()
    mock_suite.run_all.assert_called_once()


# ---------------------------------------------------------------------------
# Existing config — R/U choice
# ---------------------------------------------------------------------------

def test_existing_config_prompts_reconfigure_or_update(tmp_path):
    """Existing config prompts R/U choice."""
    from meeting_notes.core.config import AudioConfig, Config, NotionConfig

    config_path = tmp_path / "config.json"
    existing_config = Config(
        audio=AudioConfig(system_device_index=1, microphone_device_index=2),
        notion=NotionConfig(token="ntn_existing", parent_page_id="page_existing"),
    )
    existing_config.save(config_path)

    runner = CliRunner()

    with (
        patch("meeting_notes.cli.commands.init.get_config_dir", return_value=tmp_path),
        patch("meeting_notes.cli.commands.init.subprocess.run"),
        patch("meeting_notes.cli.commands.init.HealthCheckSuite") as mock_suite_cls,
    ):
        mock_suite = MagicMock()
        mock_suite.run_all.return_value = []
        mock_suite_cls.return_value = mock_suite

        # Choose U and accept all current values (empty input selects default/none)
        result = runner.invoke(
            init,
            obj={"quiet": False},
            input="U\n\n",  # U choice, then nothing for field menu
        )

    assert result.exit_code == 0, result.output
    assert "Config already exists" in result.output


def test_r_choice_runs_full_wizard(tmp_path):
    """R choice runs full wizard from scratch."""
    from meeting_notes.core.config import AudioConfig, Config, NotionConfig

    config_path = tmp_path / "config.json"
    existing_config = Config(
        audio=AudioConfig(system_device_index=1, microphone_device_index=2),
        notion=NotionConfig(token="ntn_old", parent_page_id="page_old"),
    )
    existing_config.save(config_path)

    runner = CliRunner()

    with (
        patch("meeting_notes.cli.commands.init._parse_audio_devices", return_value=FAKE_DEVICES),
        patch("meeting_notes.cli.commands.init.NotionClient") as mock_nc,
        patch("meeting_notes.cli.commands.init.subprocess.run"),
        patch("meeting_notes.cli.commands.init.HealthCheckSuite") as mock_suite_cls,
        patch("meeting_notes.cli.commands.init.get_config_dir", return_value=tmp_path),
        patch("meeting_notes.cli.commands.init.ensure_dirs"),
    ):
        mock_nc.return_value.users.me.return_value = {}
        mock_suite = MagicMock()
        mock_suite.run_all.return_value = []
        mock_suite_cls.return_value = mock_suite

        # R choice, then full wizard inputs
        result = runner.invoke(
            init,
            obj={"quiet": False},
            input="R\n1\n2\nntn_new\npage_new\n",
        )

    assert result.exit_code == 0, result.output
    # Should run the audio device selection and notion prompts
    assert "Audio Devices" in result.output or "System audio" in result.output


def test_u_choice_shows_numbered_field_menu(tmp_path):
    """U choice shows numbered field menu with current values."""
    import json
    from meeting_notes.core.config import AudioConfig, Config, NotionConfig

    config_path = tmp_path / "config.json"
    existing_config = Config(
        audio=AudioConfig(system_device_index=1, microphone_device_index=2),
        notion=NotionConfig(token="ntn_abc123xyz", parent_page_id="page_123"),
    )
    existing_config.save(config_path)

    runner = CliRunner()

    with (
        patch("meeting_notes.cli.commands.init.get_config_dir", return_value=tmp_path),
        patch("meeting_notes.cli.commands.init.subprocess.run"),
        patch("meeting_notes.cli.commands.init.HealthCheckSuite") as mock_suite_cls,
    ):
        mock_suite = MagicMock()
        mock_suite.run_all.return_value = []
        mock_suite_cls.return_value = mock_suite

        # U choice, then submit empty (accept all current, no fields to update)
        result = runner.invoke(
            init,
            obj={"quiet": False},
            input="U\n\n",
        )

    assert result.exit_code == 0, result.output
    # Field menu items should be visible
    assert "[1]" in result.output
    assert "[2]" in result.output
    assert "[3]" in result.output


# ---------------------------------------------------------------------------
# Notion token validation
# ---------------------------------------------------------------------------

def test_notion_token_valid_accepted(tmp_path):
    """Valid token is accepted (mock client.users.me() success)."""
    runner = CliRunner()

    with (
        patch("meeting_notes.cli.commands.init._parse_audio_devices", return_value=FAKE_DEVICES),
        patch("meeting_notes.cli.commands.init.NotionClient") as mock_nc,
        patch("meeting_notes.cli.commands.init.subprocess.run"),
        patch("meeting_notes.cli.commands.init.HealthCheckSuite") as mock_suite_cls,
        patch("meeting_notes.cli.commands.init.get_config_dir", return_value=tmp_path),
        patch("meeting_notes.cli.commands.init.ensure_dirs"),
    ):
        mock_nc.return_value.users.me.return_value = {"id": "user-1"}
        mock_suite = MagicMock()
        mock_suite.run_all.return_value = []
        mock_suite_cls.return_value = mock_suite

        result = runner.invoke(
            init,
            obj={"quiet": False},
            input="1\n2\nntn_valid_token\npage_id_here\n",
        )

    assert result.exit_code == 0, result.output
    assert "valid" in result.output.lower()


def test_notion_token_invalid_prompts_reentry(tmp_path):
    """Invalid token prompts re-entry (mock APIResponseError)."""
    runner = CliRunner()

    call_count = {"n": 0}

    def users_me_side_effect():
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise _fake_notion_error()
        return {"id": "user-ok"}

    with (
        patch("meeting_notes.cli.commands.init._parse_audio_devices", return_value=FAKE_DEVICES),
        patch("meeting_notes.cli.commands.init.NotionClient") as mock_nc,
        patch("meeting_notes.cli.commands.init.subprocess.run"),
        patch("meeting_notes.cli.commands.init.HealthCheckSuite") as mock_suite_cls,
        patch("meeting_notes.cli.commands.init.get_config_dir", return_value=tmp_path),
        patch("meeting_notes.cli.commands.init.ensure_dirs"),
    ):
        mock_nc.return_value.users.me.side_effect = users_me_side_effect
        mock_suite = MagicMock()
        mock_suite.run_all.return_value = []
        mock_suite_cls.return_value = mock_suite

        # First token is invalid → should re-prompt → second token is valid
        result = runner.invoke(
            init,
            obj={"quiet": False},
            input="1\n2\nbad_token\ngood_token\npage_id\n",
        )

    assert result.exit_code == 0, result.output
    assert "invalid" in result.output.lower() or "try again" in result.output.lower()
    assert call_count["n"] == 2


def test_notion_token_network_error_saves_with_warning(tmp_path):
    """Network error during token validation saves token with warning (no loop)."""
    runner = CliRunner()

    with (
        patch("meeting_notes.cli.commands.init._parse_audio_devices", return_value=FAKE_DEVICES),
        patch("meeting_notes.cli.commands.init.NotionClient") as mock_nc,
        patch("meeting_notes.cli.commands.init.subprocess.run"),
        patch("meeting_notes.cli.commands.init.HealthCheckSuite") as mock_suite_cls,
        patch("meeting_notes.cli.commands.init.get_config_dir", return_value=tmp_path),
        patch("meeting_notes.cli.commands.init.ensure_dirs"),
    ):
        mock_nc.return_value.users.me.side_effect = ConnectionError("Network error")
        mock_suite = MagicMock()
        mock_suite.run_all.return_value = []
        mock_suite_cls.return_value = mock_suite

        result = runner.invoke(
            init,
            obj={"quiet": False},
            input="1\n2\nntn_tok\npage_id\n",
        )

    assert result.exit_code == 0, result.output
    # Should say something about "saving anyway" or "could not verify"
    assert "saving" in result.output.lower() or "verify" in result.output.lower()
    # Config should still be saved
    assert (tmp_path / "config.json").exists()


# ---------------------------------------------------------------------------
# Device menu parsing
# ---------------------------------------------------------------------------

def test_device_menu_shows_numbered_list(tmp_path):
    """Device menu parses ffmpeg output into numbered list with actual device indices."""
    runner = CliRunner()

    with (
        patch("meeting_notes.cli.commands.init._parse_audio_devices", return_value=FAKE_DEVICES),
        patch("meeting_notes.cli.commands.init.NotionClient") as mock_nc,
        patch("meeting_notes.cli.commands.init.subprocess.run"),
        patch("meeting_notes.cli.commands.init.HealthCheckSuite") as mock_suite_cls,
        patch("meeting_notes.cli.commands.init.get_config_dir", return_value=tmp_path),
        patch("meeting_notes.cli.commands.init.ensure_dirs"),
    ):
        mock_nc.return_value.users.me.return_value = {}
        mock_suite = MagicMock()
        mock_suite.run_all.return_value = []
        mock_suite_cls.return_value = mock_suite

        result = runner.invoke(
            init,
            obj={"quiet": False},
            input="1\n2\nntn_tok\npage_id\n",
        )

    assert result.exit_code == 0, result.output
    assert "BlackHole 2ch" in result.output
    assert "MacBook Air Microphone" in result.output
    assert "[0]" in result.output
    assert "[1]" in result.output
    assert "[2]" in result.output
