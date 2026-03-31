"""Wave 0 test stubs for GUI worker thread requirements.

All stubs are skipped pending implementation in Wave 1+.
Requirements: SESS-06, SESS-07 (worker thread safety).
"""
import pytest


@pytest.mark.skip(reason="Wave 0 stub -- implementation pending")
def test_transcribe_worker_signals(qt_app):
    """SESS-06: TranscribeWorker emits progress, finished(stem, word_count) signals with monkeypatched transcribe_audio.

    With transcribe_audio monkeypatched to return immediately, TranscribeWorker
    should emit at least one progress(str) signal followed by a
    finished(stem: str, word_count: int) signal. The worker must run in a
    QThread and not block the main thread.
    """
    pass


@pytest.mark.skip(reason="Wave 0 stub -- implementation pending")
def test_summarize_worker_signals(qt_app):
    """SESS-07: SummarizeWorker emits progress, finished(notion_url) signals with monkeypatched service layer.

    With the summarize service layer monkeypatched, SummarizeWorker should emit
    at least one progress(str) signal followed by a finished(notion_url: str)
    signal. The worker must run in a QThread. notion_url may be None if Notion
    is not configured.
    """
    pass


@pytest.mark.skip(reason="Wave 0 stub -- implementation pending")
def test_worker_failed_signal(qt_app):
    """Worker emits failed(str) on exception.

    When the underlying service call raises an exception, both TranscribeWorker
    and SummarizeWorker must emit failed(error_message: str) instead of
    finished(). No unhandled exceptions should propagate out of the QThread.
    """
    pass


@pytest.mark.skip(reason="Wave 0 stub -- implementation pending")
def test_worker_no_ml_import_at_module_level(qt_app):
    """Importing worker modules does not add mlx_whisper/pyannote/torchaudio to sys.modules.

    Worker modules (transcribe_worker.py, summarize_worker.py) must use
    lazy imports — heavy ML dependencies are only imported inside the run()
    method, not at module import time. This prevents slow startup times and
    import errors when dependencies are not installed.
    """
    pass
