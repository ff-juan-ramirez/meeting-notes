"""Unit tests for NotionTokenCheck and NotionDatabaseCheck health checks."""
from unittest.mock import MagicMock, patch

import httpx
import pytest

from meeting_notes.core.health_check import CheckStatus


def _make_api_error(status: int, code: str = "unauthorized") -> "APIResponseError":
    """Helper to create an APIResponseError for testing."""
    from notion_client.errors import APIResponseError
    headers = httpx.Headers({"content-type": "application/json"})
    return APIResponseError(
        code=code,
        status=status,
        message=f"HTTP {status}",
        headers=headers,
        raw_body_text="{}",
    )


# ---------------------------------------------------------------------------
# NotionTokenCheck tests
# ---------------------------------------------------------------------------

def test_notion_token_check_missing():
    """NotionTokenCheck(token=None).check() returns WARNING with 'not configured' message."""
    from meeting_notes.services.checks import NotionTokenCheck
    result = NotionTokenCheck(token=None).check()
    assert result.status == CheckStatus.WARNING
    assert "not configured" in result.message
    assert "meet init" in result.fix_suggestion


@patch("meeting_notes.services.checks.NotionClient")
def test_notion_token_check_valid(mock_client_cls):
    """NotionTokenCheck with valid token returns OK after successful API call."""
    from meeting_notes.services.checks import NotionTokenCheck
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    result = NotionTokenCheck(token="secret_test").check()
    assert result.status == CheckStatus.OK
    mock_client.users.me.assert_called_once()


@patch("meeting_notes.services.checks.NotionClient")
def test_notion_token_check_invalid(mock_client_cls):
    """NotionTokenCheck returns WARNING when API call raises APIResponseError (e.g. 401)."""
    from meeting_notes.services.checks import NotionTokenCheck
    mock_client = MagicMock()
    mock_client.users.me.side_effect = _make_api_error(status=401, code="unauthorized")
    mock_client_cls.return_value = mock_client
    result = NotionTokenCheck(token="bad_token").check()
    assert result.status == CheckStatus.WARNING


@patch("meeting_notes.services.checks.NotionClient")
def test_notion_token_check_unreachable(mock_client_cls):
    """NotionTokenCheck returns WARNING when API raises a generic Exception."""
    from meeting_notes.services.checks import NotionTokenCheck
    mock_client = MagicMock()
    mock_client.users.me.side_effect = Exception("Network unreachable")
    mock_client_cls.return_value = mock_client
    result = NotionTokenCheck(token="some_token").check()
    assert result.status == CheckStatus.WARNING


# ---------------------------------------------------------------------------
# NotionDatabaseCheck tests
# ---------------------------------------------------------------------------

def test_notion_database_check_missing_page_id():
    """NotionDatabaseCheck returns WARNING when parent_page_id is None."""
    from meeting_notes.services.checks import NotionDatabaseCheck
    result = NotionDatabaseCheck(token="some_token", parent_page_id=None).check()
    assert result.status == CheckStatus.WARNING


def test_notion_database_check_missing_token():
    """NotionDatabaseCheck returns WARNING when token is None even if page_id provided."""
    from meeting_notes.services.checks import NotionDatabaseCheck
    result = NotionDatabaseCheck(token=None, parent_page_id="some_page_id").check()
    assert result.status == CheckStatus.WARNING


@patch("meeting_notes.services.checks.NotionClient")
def test_notion_database_check_accessible(mock_client_cls):
    """NotionDatabaseCheck returns OK when pages.retrieve() succeeds."""
    from meeting_notes.services.checks import NotionDatabaseCheck
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    result = NotionDatabaseCheck(token="valid_token", parent_page_id="page123").check()
    assert result.status == CheckStatus.OK
    mock_client.pages.retrieve.assert_called_once_with(page_id="page123")


@patch("meeting_notes.services.checks.NotionClient")
def test_notion_database_check_inaccessible(mock_client_cls):
    """NotionDatabaseCheck returns WARNING when pages.retrieve() raises APIResponseError."""
    from meeting_notes.services.checks import NotionDatabaseCheck
    mock_client = MagicMock()
    mock_client.pages.retrieve.side_effect = _make_api_error(status=403, code="restricted_resource")
    mock_client_cls.return_value = mock_client
    result = NotionDatabaseCheck(token="valid_token", parent_page_id="bad_page").check()
    assert result.status == CheckStatus.WARNING


# ---------------------------------------------------------------------------
# Doctor registration test
# ---------------------------------------------------------------------------

def test_doctor_registers_notion_checks():
    """doctor command registers NotionTokenCheck and NotionDatabaseCheck."""
    import meeting_notes.cli.commands.doctor as doctor_module
    source = open(doctor_module.__file__).read()
    assert "NotionTokenCheck" in source
    assert "NotionDatabaseCheck" in source
    assert "suite.register(NotionTokenCheck" in source
    assert "suite.register(NotionDatabaseCheck" in source
