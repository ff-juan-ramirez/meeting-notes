"""GUI application entry point — meet-gui command."""
import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from meeting_notes.gui.main_window import MainWindow
from meeting_notes.gui.theme import APP_STYLESHEET
from meeting_notes.core.config import Config
from meeting_notes.core.storage import get_config_dir, ensure_dirs


def main():
    """Launch the Meeting Notes GUI application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Meeting Notes")
    app.setApplicationDisplayName("Meeting Notes")
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app.setStyleSheet(APP_STYLESHEET)

    config_path = get_config_dir() / "config.json"
    config = Config.load(config_path)
    ensure_dirs(config.storage_path)

    window = MainWindow(config, config_path)
    window.setMinimumSize(900, 600)
    window.resize(1100, 700)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
