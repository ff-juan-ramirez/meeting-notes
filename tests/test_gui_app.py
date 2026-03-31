"""Tests for GUI-01: meet-gui startup does not import ML modules."""
import importlib
import sys


def test_gui_app_no_ml_imports():
    """Importing gui.app must not pull in mlx_whisper, pyannote, or torchaudio."""
    # Remove any cached imports
    ml_modules = ["mlx_whisper", "pyannote", "pyannote.audio", "torchaudio"]
    for mod in ml_modules:
        sys.modules.pop(mod, None)

    # Import the GUI app module
    import meeting_notes.gui.app  # noqa: F401
    importlib.reload(meeting_notes.gui.app)

    # Verify no ML module was loaded
    for mod in ml_modules:
        assert mod not in sys.modules, (
            f"GUI startup imported '{mod}' — this breaks the < 2s launch requirement (GUI-01). "
            f"Move this import inside a QThread.run() method."
        )


def test_gui_app_main_is_callable():
    """The main() entry point must be importable and callable."""
    from meeting_notes.gui.app import main
    assert callable(main)
