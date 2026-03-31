"""Tests for GUI-03: all visual constants centralized in theme.py."""
import re
from pathlib import Path


def test_theme_exports_colors():
    from meeting_notes.gui.theme import COLORS
    required = ["sidebar_bg", "accent", "text_primary", "green", "red", "yellow", "card_bg", "border", "input_bg"]
    for key in required:
        assert key in COLORS, f"COLORS missing required key: {key}"


def test_theme_exports_fonts():
    from meeting_notes.gui.theme import FONTS
    required = ["h1", "h2", "body", "mono", "small"]
    for key in required:
        assert key in FONTS, f"FONTS missing required key: {key}"
        family, size, weight = FONTS[key]
        assert isinstance(family, str)
        assert isinstance(size, int)
        assert weight in ("bold", "normal")


def test_theme_exports_stylesheet():
    from meeting_notes.gui.theme import APP_STYLESHEET
    assert isinstance(APP_STYLESHEET, str)
    assert "QMainWindow" in APP_STYLESHEET
    assert "#sidebar" in APP_STYLESHEET


def test_no_color_hex_in_views():
    """No hex color codes (#RRGGBB) in view files — all must be in theme.py."""
    views_dir = Path(__file__).parent.parent / "meeting_notes" / "gui" / "views"
    if not views_dir.exists():
        pytest.skip("GUI views directory not yet created")
    hex_pattern = re.compile(r'#[0-9A-Fa-f]{6}')
    violations = []
    for py_file in views_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        content = py_file.read_text()
        matches = hex_pattern.findall(content)
        if matches:
            violations.append(f"{py_file.name}: {matches}")
    assert not violations, f"Hex color codes found outside theme.py: {violations}"


def test_no_font_family_in_views():
    """No font family strings (Helvetica Neue, Menlo) in view files."""
    views_dir = Path(__file__).parent.parent / "meeting_notes" / "gui" / "views"
    if not views_dir.exists():
        pytest.skip("GUI views directory not yet created")
    violations = []
    for py_file in views_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        content = py_file.read_text()
        if "Helvetica" in content or "Menlo" in content:
            violations.append(py_file.name)
    assert not violations, f"Font family strings found outside theme.py: {violations}"


def test_make_label_returns_qlabel(qt_app):
    from meeting_notes.gui.theme import make_label
    label = make_label("Test", role="h1")
    from PySide6.QtWidgets import QLabel
    assert isinstance(label, QLabel)
    assert label.text() == "Test"


def test_make_button_returns_qpushbutton(qt_app):
    from meeting_notes.gui.theme import make_button
    btn = make_button("Click", style="primary")
    from PySide6.QtWidgets import QPushButton
    assert isinstance(btn, QPushButton)
    assert btn.text() == "Click"
    assert btn.property("style") == "primary"
