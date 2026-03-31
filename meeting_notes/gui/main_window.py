"""MainWindow — sidebar navigation + QStackedWidget container."""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout,
    QListWidget, QStackedWidget,
)
from PySide6.QtCore import Slot

from meeting_notes.gui.views.dashboard import DashboardView
from meeting_notes.gui.views.sessions import SessionsView
from meeting_notes.gui.views.record import RecordView
from meeting_notes.gui.views.templates import TemplatesView
from meeting_notes.gui.views.settings import SettingsView
from meeting_notes.gui.views.doctor import DoctorView


# Sidebar items in spec order (index matches QStackedWidget index)
SIDEBAR_ITEMS = [
    "Dashboard",      # 0
    "Sessions",       # 1
    "Record",         # 2
    "Templates",      # 3
    "Settings",       # 4
    "Health Check",   # 5
]


class MainWindow(QMainWindow):
    """Main application window with sidebar navigation."""

    def __init__(self, config, config_path, parent=None):
        super().__init__(parent)
        self._config = config
        self._config_path = config_path
        self._build_ui()

    def _build_ui(self):
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        self._sidebar = QListWidget()
        self._sidebar.setObjectName("sidebar")
        self._sidebar.setFixedWidth(180)
        for item_text in SIDEBAR_ITEMS:
            self._sidebar.addItem(item_text)

        # Stacked widget (one view per sidebar item)
        self._stack = QStackedWidget()

        # Create views — order MUST match SIDEBAR_ITEMS indices
        self._views = [
            DashboardView(self._config, parent=self),
            SessionsView(self._config, parent=self),
            RecordView(self._config, parent=self),
            TemplatesView(self._config, parent=self),
            SettingsView(self._config, parent=self),
            DoctorView(self._config, parent=self),
        ]
        for view in self._views:
            self._stack.addWidget(view)

        # Layout: sidebar left, stack right
        layout.addWidget(self._sidebar)
        layout.addWidget(self._stack, stretch=1)

        # Connect sidebar selection to stack switch
        self._sidebar.currentRowChanged.connect(self._on_sidebar_changed)

        # Cross-view navigation (Dashboard -> Sessions, Dashboard -> Record)
        dashboard_view = self._views[0]
        sessions_view = self._views[1]
        dashboard_view.navigate_requested.connect(self.navigate_to)
        dashboard_view.session_selected.connect(sessions_view.select_session)

        # Default to Dashboard (index 0)
        self._sidebar.setCurrentRow(0)

    @Slot(int)
    def navigate_to(self, index: int) -> None:
        """Switch to the view at the given sidebar index."""
        self._sidebar.setCurrentRow(index)

    @Slot(int)
    def _on_sidebar_changed(self, index: int):
        """Switch the stacked widget to the selected sidebar item."""
        self._stack.setCurrentIndex(index)
