"""Centralized theme: colors, fonts, QSS stylesheet, and factory functions.

All visual constants for the Meeting Notes GUI live in this file.
No color hex codes, font family strings, or QSS snippets are allowed
in view, widget, or worker files. Use the factory functions or
APP_STYLESHEET instead.
"""
from PySide6.QtWidgets import QLabel, QPushButton
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

# ---------------------------------------------------------------------------
# Color palette (source: GUI-MILESTONE-PLAN.md + 01-UI-SPEC.md)
# ---------------------------------------------------------------------------
COLORS = {
    "sidebar_bg":    "#1C1C1E",
    "accent":        "#0A84FF",
    "text_primary":  "#1C1C1E",
    "green":         "#30D158",
    "red":           "#FF3B30",
    "yellow":        "#FF9F0A",
    "card_bg":       "#F9F9FB",
    "border":        "#E5E5EA",
    "input_bg":      "#F2F2F7",
    "surface":       "#F5F5F7",
}

# ---------------------------------------------------------------------------
# Font specs (source: GUI-MILESTONE-PLAN.md FONTS dict + 01-UI-SPEC.md)
# All sizes in points (Qt uses pt for font sizes).
# Only h1 and h2 use bold weight. All others use normal (400).
# ---------------------------------------------------------------------------
FONTS = {
    "h1":    ("Helvetica Neue", 20, "bold"),
    "h2":    ("Helvetica Neue", 13, "bold"),
    "body":  ("Helvetica Neue", 11, "normal"),
    "mono":  ("Menlo", 10, "normal"),
    "small": ("Helvetica Neue", 9, "normal"),
}

# ---------------------------------------------------------------------------
# QSS Stylesheet (source: GUI-MILESTONE-PLAN.md + 01-UI-SPEC.md Component Inventory)
# Applied once via app.setStyleSheet(APP_STYLESHEET) in app.py.
# ---------------------------------------------------------------------------
APP_STYLESHEET = """
QMainWindow {
    background: #F5F5F7;
}

QListWidget#sidebar {
    background: #1C1C1E;
    border: none;
    outline: none;
}

QListWidget#sidebar::item {
    color: #FFFFFF;
    padding: 8px 16px;
    min-height: 40px;
}

QListWidget#sidebar::item:selected {
    background: #0A84FF;
    border-radius: 6px;
}

QPushButton[style="primary"] {
    background: #0A84FF;
    color: white;
    border-radius: 6px;
    font-weight: bold;
    padding: 8px 16px;
    border: none;
}

QPushButton[style="primary"]:hover {
    background: #0077E6;
}

QPushButton[style="danger"] {
    background: #FF3B30;
    color: white;
    border-radius: 6px;
    font-weight: bold;
    padding: 8px 16px;
    border: none;
}

QPushButton[style="danger"]:hover {
    background: #E6352B;
}

QFrame[style="card"] {
    background: #F9F9FB;
    border: 1px solid #E5E5EA;
    border-radius: 8px;
}

QLineEdit {
    background: #F2F2F7;
    border: 1px solid #E5E5EA;
    border-radius: 6px;
    padding: 4px 8px;
}

QPlainTextEdit[style="mono"] {
    font-family: Menlo;
    font-size: 10pt;
    background: #F2F2F7;
    border: 1px solid #E5E5EA;
    border-radius: 6px;
}

QFrame[style="pill-idle"] {
    background: #E5E5EA;
    border-radius: 12px;
    padding: 4px 8px;
}

QFrame[style="pill-recording"] {
    background: #FF3B30;
    border-radius: 12px;
    padding: 4px 8px;
}

QFrame[style="step-done"] {
    background: #30D158;
    border-radius: 12px;
    min-width: 24px; min-height: 24px;
    max-width: 24px; max-height: 24px;
}

QFrame[style="step-pending"] {
    background: #F5F5F7;
    border: 1px solid #E5E5EA;
    border-radius: 12px;
    min-width: 24px; min-height: 24px;
    max-width: 24px; max-height: 24px;
}

QFrame[style="session-row"] {
    background: #F9F9FB;
    border: 1px solid #E5E5EA;
    border-radius: 6px;
    padding: 8px 16px;
}

QFrame[style="session-row"]:hover {
    border: 1px solid #0A84FF;
}

QPushButton[style="secondary"] {
    background: #F2F2F7;
    color: #1C1C1E;
    border-radius: 6px;
    padding: 8px 16px;
    border: 1px solid #E5E5EA;
}

QPushButton[style="secondary"]:hover {
    background: #E5E5EA;
}

QTabWidget::pane {
    border: 1px solid #E5E5EA;
    border-radius: 6px;
    background: #F2F2F7;
}

QComboBox {
    background: #F2F2F7;
    border: 1px solid #E5E5EA;
    border-radius: 6px;
    padding: 4px 8px;
}
"""


# ---------------------------------------------------------------------------
# Factory functions
# ---------------------------------------------------------------------------

def _get_font(role: str) -> QFont:
    """Return a QFont for the given role from the FONTS dict."""
    family, size, weight = FONTS[role]
    font = QFont(family, size)
    if weight == "bold":
        font.setBold(True)
    return font


def make_label(text: str, role: str = "body", color_key: str = "text_primary") -> QLabel:
    """Create a QLabel with the correct font and color from the theme.

    Args:
        text: Label text content.
        role: Font role key from FONTS dict (h1, h2, body, mono, small).
        color_key: Color key from COLORS dict.

    Returns:
        Styled QLabel instance.
    """
    label = QLabel(text)
    label.setFont(_get_font(role))
    color = COLORS.get(color_key, COLORS["text_primary"])
    label.setStyleSheet(f"color: {color}; background: transparent;")
    return label


def make_button(text: str, style: str = "primary") -> QPushButton:
    """Create a QPushButton with the QSS style property set.

    Args:
        text: Button label text.
        style: QSS property value — "primary" or "danger".

    Returns:
        QPushButton with the style property set for QSS targeting.
    """
    button = QPushButton(text)
    button.setProperty("style", style)
    return button
