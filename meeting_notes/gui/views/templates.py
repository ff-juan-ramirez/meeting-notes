"""Templates view — placeholder for Phase 01."""
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt

from meeting_notes.gui.theme import make_label


class TemplatesView(QWidget):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self._config = config
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        label = make_label("Templates", role="h1")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
