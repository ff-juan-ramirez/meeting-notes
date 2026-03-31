"""StatusPill — compact pill widget for displaying recording state.

Shows "Idle" in a gray pill or "● Recording • H:MM:SS" in a red pill.
Used by DashboardView to reflect live recording state polled from state.json.
"""
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel
from PySide6.QtGui import QFont

from meeting_notes.gui.theme import COLORS


class StatusPill(QFrame):
    """Compact pill indicator for recording state.

    Switches between two visual states via the QSS ``style`` property:
    - ``pill-idle``: gray background (#E5E5EA), "Idle" text, dark text
    - ``pill-recording``: red background (#FF3B30), "● Recording • H:MM:SS" text, white text

    The unpolish/polish cycle forces Qt to re-evaluate the QSS property
    selector after the property value changes at runtime.

    Args:
        parent: Optional parent widget.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(24)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(0)

        self._label = QLabel()
        # font-small: 10pt Menlo per UI-SPEC typography table
        self._label.setFont(QFont("Menlo", 10))
        layout.addWidget(self._label)

        # Establish initial idle state
        self.set_idle()

    # -------------------------------------------------------------------------
    # State transitions
    # -------------------------------------------------------------------------

    def set_idle(self) -> None:
        """Switch pill to idle state (gray background, dark text)."""
        self.setProperty("style", "pill-idle")
        self.style().unpolish(self)
        self.style().polish(self)
        self._label.setText("Idle")
        self._label.setStyleSheet(
            f"color: {COLORS['text_primary']}; background: transparent;"
        )

    def set_recording(self, elapsed: str) -> None:
        """Switch pill to recording state (red background, white text).

        Args:
            elapsed: Formatted elapsed time string, e.g. "0:05:23" or "1:02:45".
        """
        self.setProperty("style", "pill-recording")
        self.style().unpolish(self)
        self.style().polish(self)
        self._label.setText(f"\u25cf Recording \u2022 {elapsed}")
        self._label.setStyleSheet("color: #FFFFFF; background: transparent;")
