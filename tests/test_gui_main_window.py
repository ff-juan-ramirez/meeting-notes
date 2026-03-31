"""Tests for GUI-02: sidebar navigates to all 6 views."""
import pytest
from meeting_notes.core.config import Config


@pytest.fixture
def main_window(qt_app):
    from meeting_notes.gui.main_window import MainWindow
    config = Config()
    window = MainWindow(config, None)
    yield window
    window.close()


def test_main_window_has_6_sidebar_items(main_window):
    """Sidebar must have exactly 6 items."""
    assert main_window._sidebar.count() == 6


def test_main_window_has_6_views(main_window):
    """QStackedWidget must have exactly 6 views."""
    assert main_window._stack.count() == 6


def test_main_window_default_is_dashboard(main_window):
    """Default selected sidebar item is Dashboard (index 0)."""
    assert main_window._sidebar.currentRow() == 0
    assert main_window._stack.currentIndex() == 0


def test_main_window_sidebar_navigation(main_window):
    """Clicking each sidebar item switches the stacked widget."""
    for i in range(6):
        main_window._sidebar.setCurrentRow(i)
        assert main_window._stack.currentIndex() == i, (
            f"Sidebar item {i} did not switch stack to index {i}"
        )


def test_main_window_sidebar_labels(main_window):
    """Sidebar items have the exact labels from the spec."""
    expected = ["Dashboard", "Sessions", "Record", "Templates", "Settings", "Health Check"]
    for i, label in enumerate(expected):
        assert main_window._sidebar.item(i).text() == label


def test_main_window_sidebar_width(main_window):
    """Sidebar width is fixed at 180px (setFixedWidth sets both min and max)."""
    assert main_window._sidebar.minimumWidth() == 180 and main_window._sidebar.maximumWidth() == 180
