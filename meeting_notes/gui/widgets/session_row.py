"""SessionRowWidget — single row for the Sessions list view.

Displays session title, date + duration subtitle, and a status color dot.
Used by SessionsView to populate the QListWidget session list.

Do NOT import from services or CLI modules — this widget is pure presentation.
"""
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout
from PySide6.QtCore import QSize, Qt

from meeting_notes.gui.theme import COLORS, make_label


# Status dot colors by session status
_STATUS_DOT_COLORS: dict[str, str] = {
    "summarized": COLORS["green"],       # #30D158
    "transcribed": COLORS["accent"],     # #0A84FF
    "not-transcribed": COLORS["border"], # #E5E5EA
}


class SessionRowWidget(QFrame):
    """A single session row for display in the Sessions list.

    Shows a title line (body role, 11pt Helvetica Neue normal) and a subtitle
    line (small role, 9pt for date + duration + status text) on the left, with
    a small 8x8px color dot on the right indicating session status.

    Args:
        session_id: Unique session identifier (WAV stem).
        title: Display title derived from session metadata or filename.
        subtitle: Date + duration string (e.g., "2026-03-24 · 42m 30s").
        status: One of "summarized", "transcribed", "not-transcribed".
        parent: Optional parent widget.
    """

    def __init__(
        self,
        session_id: str,
        title: str,
        subtitle: str,
        status: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._session_id = session_id

        # Apply QSS property selector for theme targeting
        self.setProperty("style", "session-row")

        # --- Layout ----------------------------------------------------------
        h_layout = QHBoxLayout(self)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(8)

        # Left: title + subtitle labels stacked vertically
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        title_label = make_label(title, role="body")
        title_label.setWordWrap(False)

        subtitle_label = make_label(subtitle, role="small")
        subtitle_label.setWordWrap(False)

        text_layout.addWidget(title_label)
        text_layout.addWidget(subtitle_label)

        h_layout.addLayout(text_layout, stretch=1)

        # Right: 8x8px status dot
        dot_color = _STATUS_DOT_COLORS.get(status, COLORS["border"])
        dot = QFrame()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet(
            f"background: {dot_color}; border-radius: 4px; border: none;"
        )
        h_layout.addWidget(dot, alignment=Qt.AlignmentFlag.AlignVCenter)

    # -------------------------------------------------------------------------
    # Public interface
    # -------------------------------------------------------------------------

    @property
    def session_id(self) -> str:
        """Return the session identifier for this row."""
        return self._session_id

    def sizeHint(self) -> QSize:
        """Preferred height of 56px per UI-SPEC spacing contract."""
        return QSize(0, 56)
