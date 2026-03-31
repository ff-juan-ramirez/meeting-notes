"""SessionsView — two-panel session browser for Meeting Notes GUI.

Left panel: filterable session list with QListWidget + filter QComboBox.
Right panel: detail metadata, pipeline indicator, action buttons, content tabs.
Workers: TranscribeWorker and SummarizeWorker integrated with double-start guard.
"""
import wave
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QListWidget,
    QListWidgetItem, QStackedWidget, QLabel, QComboBox, QFrame,
    QTabWidget, QPlainTextEdit, QLineEdit, QMessageBox, QSizePolicy,
    QScrollArea,
)
from PySide6.QtCore import Qt, Slot, Signal, QSize, QUrl
from PySide6.QtGui import QDesktopServices

from meeting_notes.core.config import Config
from meeting_notes.core.state import read_state
from meeting_notes.core.storage import get_data_dir
from meeting_notes.gui.theme import make_label, make_button, COLORS
from meeting_notes.gui.widgets.session_row import SessionRowWidget
from meeting_notes.gui.workers.transcribe_worker import TranscribeWorker
from meeting_notes.gui.workers.summarize_worker import SummarizeWorker


# ---------------------------------------------------------------------------
# Module-level helper functions (duplicated from list.py to avoid CLI imports)
# ---------------------------------------------------------------------------

def _wav_duration(wav_path_str: str | None) -> int | None:
    """Read duration from WAV header. Returns None if unavailable."""
    if not wav_path_str:
        return None
    try:
        with wave.open(wav_path_str, "rb") as wf:
            return int(wf.getnframes() / wf.getframerate())
    except Exception:
        return None


def _format_duration(seconds: int | None) -> str:
    """Format seconds as MM:SS. Returns em dash if None."""
    if seconds is None:
        return "\u2014"
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"


def _derive_status(meta: dict) -> str:
    """Derive session status from metadata fields.

    Returns "summarized", "transcribed", or "not-transcribed".
    """
    notes_path = meta.get("notes_path")
    if notes_path and Path(notes_path).exists():
        return "summarized"
    transcript_path = meta.get("transcript_path")
    if transcript_path and Path(transcript_path).exists():
        return "transcribed"
    return "not-transcribed"


def _derive_title(meta: dict, stem: str) -> str:
    """Derive session title.

    Priority: recording_name > notes LLM heading > stem.
    """
    recording_name = meta.get("recording_name")
    if recording_name:
        return recording_name
    notes_path = meta.get("notes_path")
    if notes_path and Path(notes_path).exists():
        try:
            from meeting_notes.services.notion import extract_title
            notes_text = Path(notes_path).read_text()
            return extract_title(notes_text, stem)
        except Exception:
            return stem
    return stem


def _derive_date(meta: dict) -> str:
    """Derive display date from metadata. Format: YYYY-MM-DD HH:MM."""
    for field in ("transcribed_at", "summarized_at"):
        ts = meta.get(field)
        if ts:
            try:
                dt = datetime.fromisoformat(ts)
                return dt.strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                pass
    wav_path = meta.get("wav_path")
    if wav_path:
        try:
            mtime = Path(wav_path).stat().st_mtime
            return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        except (OSError, ValueError):
            pass
    return "\u2014"


def _sort_key(metadata_path: Path) -> str:
    """Sort key: transcribed_at ISO string, or WAV mtime as ISO."""
    meta = read_state(metadata_path)
    if meta:
        ts = meta.get("transcribed_at")
        if ts:
            return ts
        wav_path = meta.get("wav_path")
        if wav_path:
            try:
                mtime = Path(wav_path).stat().st_mtime
                return datetime.fromtimestamp(mtime).isoformat()
            except (OSError, ValueError):
                pass
    return ""


# ---------------------------------------------------------------------------
# SessionsView
# ---------------------------------------------------------------------------

class SessionsView(QWidget):
    """Full two-panel session browser.

    Left panel: filter QComboBox + QListWidget of SessionRowWidgets.
    Right panel: detail metadata, pipeline steps, action buttons, content tabs.
    """

    def __init__(self, config: Config, parent=None) -> None:
        super().__init__(parent)
        self._config = config
        self._sessions: list[dict] = []           # all loaded sessions
        self._filtered_sessions: list[dict] = []  # sessions after filter
        self._worker = None                        # current running worker
        self._current_session: dict | None = None  # selected session dict
        self._pipeline_frames: list[QFrame] = []  # 4 pipeline step circles
        self._build_ui()

    # -------------------------------------------------------------------------
    # UI Construction
    # -------------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Build the full two-panel layout."""
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(12)

        # Heading
        heading = make_label("Sessions", role="h1")
        root_layout.addWidget(heading)

        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        root_layout.addWidget(splitter)

        # ---- Left panel ----
        left_panel = QWidget()
        left_panel.setMinimumWidth(280)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        # Filter bar
        self._filter_combo = QComboBox()
        self._filter_combo.addItems(["All", "Recorded", "Transcribed", "Summarized"])
        self._filter_combo.currentTextChanged.connect(self._apply_filter)
        left_layout.addWidget(self._filter_combo)

        # List stack (list vs empty state)
        self._left_stack = QStackedWidget()

        # Index 0: session list
        self._list_widget = QListWidget()
        self._list_widget.currentRowChanged.connect(self._on_session_selected)
        self._left_stack.addWidget(self._list_widget)

        # Index 1: empty state
        empty_list_label = QLabel("No sessions yet. Start a recording to get started.")
        empty_list_label.setWordWrap(True)
        empty_list_label.setAlignment(Qt.AlignCenter)
        self._left_stack.addWidget(empty_list_label)

        left_layout.addWidget(self._left_stack)
        splitter.addWidget(left_panel)

        # ---- Right panel ----
        right_panel = QWidget()
        right_panel.setMinimumWidth(400)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self._detail_stack = QStackedWidget()

        # Index 0: no-selection empty state
        empty_detail_label = QLabel("Select a session to view details.")
        empty_detail_label.setAlignment(Qt.AlignCenter)
        self._detail_stack.addWidget(empty_detail_label)

        # Index 1: detail panel (inside scroll area for small windows)
        self._detail_panel = self._build_detail_panel()
        scroll = QScrollArea()
        scroll.setWidget(self._detail_panel)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self._detail_stack.addWidget(scroll)

        right_layout.addWidget(self._detail_stack)
        splitter.addWidget(right_panel)

        # Splitter proportions
        splitter.setSizes([300, 700])

    def _build_detail_panel(self) -> QWidget:
        """Build the detail panel widget (index 1 of right QStackedWidget)."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # --- Metadata section ---
        self._lbl_title = make_label("", role="h2")
        self._lbl_title.setWordWrap(True)
        layout.addWidget(self._lbl_title)

        meta_row = QHBoxLayout()
        meta_row.setSpacing(16)
        self._lbl_date = make_label("", role="small")
        self._lbl_duration = make_label("", role="small")
        self._lbl_wordcount = make_label("", role="small")
        meta_row.addWidget(self._lbl_date)
        meta_row.addWidget(self._lbl_duration)
        meta_row.addWidget(self._lbl_wordcount)
        meta_row.addStretch()
        layout.addLayout(meta_row)

        # --- Pipeline indicator ---
        pipeline_container = QHBoxLayout()
        pipeline_container.setSpacing(8)
        pipeline_container.setContentsMargins(0, 8, 0, 8)
        step_labels = ["Recorded", "Transcribed", "Summarized", "Notion"]
        self._pipeline_frames = []
        for i, label_text in enumerate(step_labels):
            step_col = QVBoxLayout()
            step_col.setSpacing(4)
            step_col.setAlignment(Qt.AlignHCenter)

            circle = QFrame()
            circle.setFixedSize(24, 24)
            circle.setProperty("style", "step-pending")
            step_col.addWidget(circle, alignment=Qt.AlignHCenter)
            self._pipeline_frames.append(circle)

            step_label = make_label(label_text, role="small")
            step_label.setAlignment(Qt.AlignHCenter)
            step_col.addWidget(step_label, alignment=Qt.AlignHCenter)

            pipeline_container.addLayout(step_col)

            if i < len(step_labels) - 1:
                arrow = make_label("\u2192", role="body")
                arrow.setAlignment(Qt.AlignVCenter)
                pipeline_container.addWidget(arrow, alignment=Qt.AlignVCenter)

        layout.addLayout(pipeline_container)

        # --- Action buttons row ---
        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(8)
        self._btn_transcribe = make_button("Transcribe", "primary")
        self._btn_transcribe.clicked.connect(self._start_transcribe)
        self._btn_summarize = make_button("Summarize", "primary")
        self._btn_summarize.clicked.connect(self._start_summarize)
        self._btn_notion = make_button("Open in Notion", "secondary")
        self._btn_notion.clicked.connect(self._open_notion)
        buttons_row.addWidget(self._btn_transcribe)
        buttons_row.addWidget(self._btn_summarize)
        buttons_row.addWidget(self._btn_notion)
        buttons_row.addStretch()
        layout.addLayout(buttons_row)

        # --- Template selector ---
        template_row = QHBoxLayout()
        template_row.setSpacing(8)
        template_row.addWidget(make_label("Template", role="body"))
        self._template_combo = QComboBox()
        self._template_combo.setMinimumWidth(160)
        template_row.addWidget(self._template_combo)
        template_row.addStretch()
        layout.addLayout(template_row)

        # --- Title override ---
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_row.addWidget(make_label("Title (optional)", role="body"))
        self._title_input = QLineEdit()
        self._title_input.setPlaceholderText("Leave blank to auto-generate")
        self._title_input.setMinimumWidth(200)
        title_row.addWidget(self._title_input)
        title_row.addStretch()
        layout.addLayout(title_row)

        # --- Status label ---
        self._status_label = make_label("", role="body")
        self._status_label.hide()
        layout.addWidget(self._status_label)

        # --- Content tabs ---
        self._tabs = QTabWidget()
        self._tab_transcript = QPlainTextEdit()
        self._tab_transcript.setReadOnly(True)
        self._tab_transcript.setProperty("style", "mono")
        self._tab_notes = QPlainTextEdit()
        self._tab_notes.setReadOnly(True)
        self._tab_notes.setProperty("style", "mono")
        self._tab_srt = QPlainTextEdit()
        self._tab_srt.setReadOnly(True)
        self._tab_srt.setProperty("style", "mono")
        self._tabs.addTab(self._tab_transcript, "Transcript")
        self._tabs.addTab(self._tab_notes, "Notes")
        self._tabs.addTab(self._tab_srt, "SRT")
        layout.addWidget(self._tabs)

        return panel

    # -------------------------------------------------------------------------
    # Qt Lifecycle
    # -------------------------------------------------------------------------

    def showEvent(self, event) -> None:
        """Refresh session list on show. Lazily populate template combo."""
        super().showEvent(event)
        self._refresh_sessions()
        if self._template_combo.count() == 0:
            try:
                from meeting_notes.services.llm import list_templates
                for t in list_templates():
                    self._template_combo.addItem(t["name"])
                if self._template_combo.count() > 0:
                    self._template_combo.setCurrentIndex(0)
            except Exception:
                pass

    def closeEvent(self, event) -> None:
        """Gracefully stop any running worker on close."""
        if self._worker is not None and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait()
        super().closeEvent(event)

    # -------------------------------------------------------------------------
    # Session Loading
    # -------------------------------------------------------------------------

    def _refresh_sessions(self) -> None:
        """Scan metadata dir, build session list, then apply filter."""
        data_dir = get_data_dir(self._config.storage_path)
        metadata_dir = data_dir / "metadata"
        self._sessions = []

        if not metadata_dir.exists():
            self._apply_filter()
            return

        json_files = sorted(
            metadata_dir.glob("*.json"),
            key=_sort_key,
            reverse=True,
        )

        for path in json_files:
            meta = read_state(path) or {}
            stem = path.stem

            duration_seconds = meta.get("duration_seconds")
            if duration_seconds is None:
                duration_seconds = _wav_duration(meta.get("wav_path"))

            status = _derive_status(meta)

            self._sessions.append({
                **meta,
                "session_id": stem,
                "title": _derive_title(meta, stem),
                "date": _derive_date(meta),
                "duration_display": _format_duration(duration_seconds),
                "duration_seconds": duration_seconds,
                "status": status,
            })

        self._apply_filter()

    @Slot(str)
    def _apply_filter(self, filter_text: str = "") -> None:
        """Filter sessions by status combo and repopulate QListWidget."""
        combo_text = self._filter_combo.currentText()

        status_map = {
            "All": None,
            "Recorded": "not-transcribed",
            "Transcribed": "transcribed",
            "Summarized": "summarized",
        }
        target_status = status_map.get(combo_text, None)

        if target_status is None:
            self._filtered_sessions = list(self._sessions)
        else:
            self._filtered_sessions = [
                s for s in self._sessions if s.get("status") == target_status
            ]

        # Repopulate list widget (suppress currentRowChanged during rebuild)
        self._list_widget.blockSignals(True)
        self._list_widget.clear()
        for session in self._filtered_sessions:
            widget = SessionRowWidget(
                session_id=session["session_id"],
                title=session["title"],
                subtitle=f"{session['date']} \u00b7 {session['duration_display']}",
                status=session["status"],
            )
            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())
            self._list_widget.addItem(item)
            self._list_widget.setItemWidget(item, widget)
        self._list_widget.blockSignals(False)

        if self._filtered_sessions:
            self._left_stack.setCurrentIndex(0)
        else:
            self._left_stack.setCurrentIndex(1)

    # -------------------------------------------------------------------------
    # Session Selection
    # -------------------------------------------------------------------------

    @Slot(int)
    def _on_session_selected(self, row: int) -> None:
        """Handle session row selection. Show detail or empty state."""
        if row < 0 or row >= len(self._filtered_sessions):
            self._current_session = None
            self._detail_stack.setCurrentIndex(0)
            return
        self._current_session = self._filtered_sessions[row]
        self._detail_stack.setCurrentIndex(1)
        self._populate_detail()

    def _populate_detail(self) -> None:
        """Populate all detail panel widgets from current session."""
        if self._current_session is None:
            return
        s = self._current_session

        # Metadata labels
        self._lbl_title.setText(s.get("title", ""))
        self._lbl_date.setText(s.get("date", "\u2014"))
        duration_display = s.get("duration_display", "\u2014")
        self._lbl_duration.setText(f"Duration: {duration_display}")
        word_count = s.get("word_count")
        self._lbl_wordcount.setText(
            f"Words: {word_count}" if word_count is not None else ""
        )

        # Pipeline steps
        wav_path = s.get("wav_path")
        transcript_path = s.get("transcript_path")
        notes_path = s.get("notes_path")
        notion_url = s.get("notion_url")

        step_done = [
            bool(wav_path and Path(wav_path).exists()),
            bool(transcript_path and Path(transcript_path).exists()),
            bool(notes_path and Path(notes_path).exists()),
            bool(notion_url),
        ]

        for frame, done in zip(self._pipeline_frames, step_done):
            new_style = "step-done" if done else "step-pending"
            frame.setProperty("style", new_style)
            # Force QSS re-evaluation
            frame.style().unpolish(frame)
            frame.style().polish(frame)
            frame.update()

        # Button states per D-01
        wav_exists = bool(wav_path and Path(wav_path).exists())
        is_transcribed = bool(transcript_path and Path(transcript_path).exists())
        is_summarized = bool(notes_path and Path(notes_path).exists())
        template_selected = self._template_combo.count() > 0

        self._btn_transcribe.setEnabled(wav_exists and not is_transcribed)
        self._btn_summarize.setEnabled(is_transcribed and template_selected)
        self._btn_notion.setEnabled(bool(notion_url))

        # Tab content
        if transcript_path and Path(transcript_path).exists():
            try:
                self._tab_transcript.setPlainText(Path(transcript_path).read_text())
            except Exception:
                self._tab_transcript.setPlainText("Not yet transcribed.")
        else:
            self._tab_transcript.setPlainText("Not yet transcribed.")

        if notes_path and Path(notes_path).exists():
            try:
                self._tab_notes.setPlainText(Path(notes_path).read_text())
            except Exception:
                self._tab_notes.setPlainText("Not yet summarized.")
        else:
            self._tab_notes.setPlainText("Not yet summarized.")

        # SRT: check metadata srt_path, then derive from transcript_path
        srt_path = s.get("srt_path")
        if not srt_path and transcript_path:
            derived_srt = transcript_path.replace(".txt", ".srt")
            if Path(derived_srt).exists():
                srt_path = derived_srt

        if srt_path and Path(srt_path).exists():
            try:
                self._tab_srt.setPlainText(Path(srt_path).read_text())
            except Exception:
                self._tab_srt.setPlainText("No SRT file.")
        else:
            self._tab_srt.setPlainText("No SRT file.")

        # Clear status label
        self._status_label.hide()
        self._status_label.setText("")

    # -------------------------------------------------------------------------
    # Worker Actions
    # -------------------------------------------------------------------------

    @Slot()
    def _start_transcribe(self) -> None:
        """Start TranscribeWorker with double-start guard."""
        if self._worker is not None and self._worker.isRunning():
            return
        if self._current_session is None:
            return
        wav_path = self._current_session.get("wav_path")
        if not wav_path:
            return

        self._worker = TranscribeWorker(Path(wav_path), self._config)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_transcribe_done)
        self._worker.failed.connect(self._on_worker_failed)
        self._worker.finished.connect(self._worker.deleteLater)
        self._set_buttons_enabled(False)
        self._status_label.show()
        self._worker.start()

    @Slot()
    def _start_summarize(self) -> None:
        """Start SummarizeWorker with double-start guard."""
        if self._worker is not None and self._worker.isRunning():
            return
        if self._current_session is None:
            return

        stem = self._current_session.get("session_id", "")
        template = self._template_combo.currentText() or "meeting"
        title_text = self._title_input.text().strip()
        title = title_text if title_text else None

        self._worker = SummarizeWorker(stem, template, title, self._config)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_summarize_done)
        self._worker.failed.connect(self._on_worker_failed)
        self._worker.finished.connect(self._worker.deleteLater)
        self._set_buttons_enabled(False)
        self._status_label.show()
        self._worker.start()

    @Slot(str)
    def _on_progress(self, msg: str) -> None:
        """Update status label with worker progress message."""
        self._status_label.setText(msg)
        self._status_label.show()

    @Slot(str, int)
    def _on_transcribe_done(self, stem: str, word_count: int) -> None:
        """Handle TranscribeWorker finished signal. Refresh detail from disk."""
        self._status_label.hide()
        self._status_label.setText("")
        self._set_buttons_enabled(True)
        # Refresh session list and detail panel
        self._refresh_sessions()
        # Re-select the same session if it matches
        if (self._current_session is not None
                and self._current_session.get("session_id") == stem):
            # Find updated session in self._sessions
            for s in self._sessions:
                if s.get("session_id") == stem:
                    self._current_session = s
                    self._populate_detail()
                    break

    @Slot(str)
    def _on_summarize_done(self, notion_url: str) -> None:
        """Handle SummarizeWorker finished signal. Refresh detail from disk."""
        self._status_label.hide()
        self._status_label.setText("")
        self._set_buttons_enabled(True)
        current_id = (self._current_session or {}).get("session_id")
        self._refresh_sessions()
        if current_id:
            for s in self._sessions:
                if s.get("session_id") == current_id:
                    self._current_session = s
                    self._populate_detail()
                    break

    @Slot(str)
    def _on_worker_failed(self, error: str) -> None:
        """Handle worker failed signal. Show QMessageBox and re-enable buttons."""
        QMessageBox.warning(
            self,
            "Operation Failed",
            f"{error}. Check your configuration and try again.",
        )
        self._status_label.hide()
        self._status_label.setText("")
        self._set_buttons_enabled(True)

    def _set_buttons_enabled(self, enabled: bool) -> None:
        """Enable or disable all three action buttons."""
        self._btn_transcribe.setEnabled(enabled)
        self._btn_summarize.setEnabled(enabled)
        self._btn_notion.setEnabled(enabled)

    @Slot()
    def _open_notion(self) -> None:
        """Open notion_url in default browser via QDesktopServices."""
        if self._current_session is None:
            return
        url = self._current_session.get("notion_url", "")
        if url:
            QDesktopServices.openUrl(QUrl(url))

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def select_session(self, session_id: str) -> None:
        """Pre-select a session by ID. Called by MainWindow for cross-view nav."""
        for row in range(self._list_widget.count()):
            item = self._list_widget.item(row)
            widget = self._list_widget.itemWidget(item)
            if isinstance(widget, SessionRowWidget) and widget.session_id == session_id:
                self._list_widget.setCurrentRow(row)
                return
