"""Dashboard view — aggregate stats, recording indicator, recent sessions."""
import wave
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QListWidget, QListWidgetItem, QStackedWidget, QSizePolicy,
)
from PySide6.QtCore import Qt, Slot, Signal, QTimer, QSize

from meeting_notes.core.config import Config
from meeting_notes.core.state import read_state, check_for_stale_session
from meeting_notes.core.storage import get_data_dir, get_config_dir
from meeting_notes.gui.theme import make_label, make_button, COLORS, FONTS
from meeting_notes.gui.widgets.badge import StatusPill
from meeting_notes.gui.widgets.session_row import SessionRowWidget


# ---------------------------------------------------------------------------
# Module-level helper functions (duplicated from sessions.py by design —
# both views are self-contained to avoid cross-imports between views)
# ---------------------------------------------------------------------------

def _wav_duration(wav_path_str: str | None) -> int | None:
    """Read duration in seconds from WAV header. Returns None if unavailable."""
    if not wav_path_str:
        return None
    try:
        with wave.open(wav_path_str, "rb") as wf:
            return int(wf.getnframes() / wf.getframerate())
    except Exception:
        return None


def _format_duration(seconds: int | None) -> str:
    """Format seconds as mm:ss. Returns em dash if None."""
    if seconds is None:
        return "\u2014"
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"


def _derive_status(meta: dict) -> str:
    """Derive session status from metadata fields.

    - not-transcribed: no transcript_path or file not found
    - transcribed: has transcript_path but no notes_path
    - summarized: has notes_path and file exists
    """
    notes_path = meta.get("notes_path")
    if notes_path and Path(notes_path).exists():
        return "summarized"
    transcript_path = meta.get("transcript_path")
    if transcript_path and Path(transcript_path).exists():
        return "transcribed"
    return "not-transcribed"


def _derive_title(meta: dict, stem: str) -> str:
    """Derive session title. Priority: recording_name > stem."""
    recording_name = meta.get("recording_name")
    if recording_name:
        return recording_name
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
    # Fallback: WAV mtime
    wav_path = meta.get("wav_path")
    if wav_path:
        try:
            mtime = Path(wav_path).stat().st_mtime
            return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        except (OSError, ValueError):
            pass
    return "\u2014"


def _sort_key(metadata_path: Path) -> str:
    """Sort key: transcribed_at ISO or WAV mtime ISO. Newest-first when reversed."""
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


def _session_datetime(meta: dict) -> datetime | None:
    """Return best available datetime for the session (timezone-aware UTC)."""
    for field in ("transcribed_at", "summarized_at"):
        ts = meta.get(field)
        if ts:
            try:
                dt = datetime.fromisoformat(ts)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except (ValueError, TypeError):
                pass
    wav_path = meta.get("wav_path")
    if wav_path:
        try:
            mtime = Path(wav_path).stat().st_mtime
            return datetime.fromtimestamp(mtime, tz=timezone.utc)
        except (OSError, ValueError):
            pass
    return None


# ---------------------------------------------------------------------------
# DashboardView
# ---------------------------------------------------------------------------

class DashboardView(QWidget):
    """Landing screen showing aggregate stats, recording state, and recent sessions."""

    # Class-level signals (per RESEARCH.md Pattern 5)
    navigate_requested = Signal(int)   # sidebar index to switch to
    session_selected = Signal(str)     # session_id for Sessions pre-select

    def __init__(self, config: Config, parent=None) -> None:
        super().__init__(parent)
        self._config = config
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(2000)
        self._poll_timer.timeout.connect(self._refresh_recording_state)
        self._build_ui()

    # -------------------------------------------------------------------------
    # UI construction
    # -------------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Build the complete dashboard layout."""
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 32, 32, 32)
        root.setSpacing(24)

        # Heading
        heading = make_label("Dashboard", role="h1")
        root.addWidget(heading)

        # --- Stats row -------------------------------------------------------
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)

        self._stat_total = self._make_stat_card(stats_row, "0", "Total Sessions")
        self._stat_transcribed = self._make_stat_card(stats_row, "0", "Transcribed")
        self._stat_summarized = self._make_stat_card(stats_row, "0", "Summarized")
        self._stat_week = self._make_stat_card(stats_row, "0", "This Week")
        stats_row.addStretch()

        root.addLayout(stats_row)

        # --- Recording state row ---------------------------------------------
        rec_row = QHBoxLayout()
        rec_row.setSpacing(16)
        rec_row.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self._recording_pill = StatusPill()
        rec_row.addWidget(self._recording_pill)

        self._recording_btn = make_button("Start Recording", "primary")
        self._recording_btn.clicked.connect(
            lambda: self.navigate_requested.emit(2)
        )
        rec_row.addWidget(self._recording_btn)
        rec_row.addStretch()

        root.addLayout(rec_row)

        # --- Recent sessions -------------------------------------------------
        recent_heading = make_label("Recent Sessions", role="h2")
        root.addWidget(recent_heading)

        # QStackedWidget: index 0 = list, index 1 = empty state label
        self._recent_stack = QStackedWidget()

        self._recent_list = QListWidget()
        self._recent_list.setSpacing(4)
        self._recent_list.setSelectionMode(
            QListWidget.SelectionMode.SingleSelection
        )
        self._recent_list.currentRowChanged.connect(self._on_recent_session_clicked)
        self._recent_stack.addWidget(self._recent_list)  # index 0

        empty_label = QLabel("No sessions yet.")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._recent_stack.addWidget(empty_label)  # index 1

        root.addWidget(self._recent_stack)
        root.addStretch()

    def _make_stat_card(
        self,
        parent_layout: QHBoxLayout,
        count_text: str,
        label_text: str,
    ) -> QLabel:
        """Create a stat card, add to parent_layout, return the count QLabel."""
        card = QFrame()
        card.setProperty("style", "card")
        card.setMinimumWidth(120)
        card.setMinimumHeight(80)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(4)

        count_label = make_label(count_text, role="h1")
        desc_label = make_label(label_text, role="small")

        card_layout.addWidget(count_label)
        card_layout.addWidget(desc_label)

        parent_layout.addWidget(card)
        return count_label

    # -------------------------------------------------------------------------
    # Qt lifecycle hooks
    # -------------------------------------------------------------------------

    def showEvent(self, event) -> None:
        """Refresh data and start polling timer when view becomes visible."""
        super().showEvent(event)
        self._refresh_dashboard()
        self._poll_timer.start()

    def hideEvent(self, event) -> None:
        """Stop polling timer when view is hidden (optional optimization)."""
        super().hideEvent(event)
        self._poll_timer.stop()

    # -------------------------------------------------------------------------
    # Data refresh
    # -------------------------------------------------------------------------

    def _refresh_dashboard(self) -> None:
        """Reload session stats and recent sessions from disk."""
        storage_path = getattr(self._config, "storage_path", None)
        data_dir = get_data_dir(storage_path)
        metadata_dir = data_dir / "metadata"

        if not metadata_dir.exists():
            self._stat_total.setText("0")
            self._stat_transcribed.setText("0")
            self._stat_summarized.setText("0")
            self._stat_week.setText("0")
            self._recent_list.clear()
            self._recent_stack.setCurrentIndex(1)
            return

        json_files = sorted(metadata_dir.glob("*.json"), key=_sort_key, reverse=True)

        total_count = 0
        transcribed_count = 0
        summarized_count = 0
        week_count = 0
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)

        sessions_data = []
        for path in json_files:
            meta = read_state(path) or {}
            stem = path.stem
            total_count += 1

            status = _derive_status(meta)
            if status in ("transcribed", "summarized"):
                transcribed_count += 1
            if status == "summarized":
                summarized_count += 1

            session_dt = _session_datetime(meta)
            if session_dt and session_dt >= week_ago:
                week_count += 1

            sessions_data.append((stem, meta, status))

        # Update stat labels
        self._stat_total.setText(str(total_count))
        self._stat_transcribed.setText(str(transcribed_count))
        self._stat_summarized.setText(str(summarized_count))
        self._stat_week.setText(str(week_count))

        # Populate recent sessions (up to 5, already sorted newest-first)
        self._recent_list.clear()
        recent_5 = sessions_data[:5]

        if not recent_5:
            self._recent_stack.setCurrentIndex(1)
            return

        self._recent_stack.setCurrentIndex(0)
        for stem, meta, status in recent_5:
            title = _derive_title(meta, stem)
            date_str = _derive_date(meta)
            duration_seconds = meta.get("duration_seconds") or _wav_duration(
                meta.get("wav_path")
            )
            subtitle = f"{date_str} \u00b7 {_format_duration(duration_seconds)}"

            row_widget = SessionRowWidget(
                session_id=stem,
                title=title,
                subtitle=subtitle,
                status=status,
            )

            item = QListWidgetItem(self._recent_list)
            item.setSizeHint(row_widget.sizeHint())
            self._recent_list.addItem(item)
            self._recent_list.setItemWidget(item, row_widget)

        # Refresh recording state after rebuilding list
        self._refresh_recording_state()

    @Slot()
    def _refresh_recording_state(self) -> None:
        """Poll state.json and update pill + button to reflect current recording state."""
        config_dir = get_config_dir()
        state_path = config_dir / "state.json"
        state = read_state(state_path)

        if state and check_for_stale_session(state):
            start_time_str = state.get("start_time", "")
            try:
                start = datetime.fromisoformat(start_time_str)
                if start.tzinfo is None:
                    start = start.replace(tzinfo=timezone.utc)
                elapsed = int(
                    (datetime.now(timezone.utc) - start).total_seconds()
                )
                mins, secs = divmod(elapsed, 60)
                hours, mins = divmod(mins, 60)
                elapsed_str = f"{hours}:{mins:02d}:{secs:02d}"
                self._recording_pill.set_recording(elapsed_str)
                self._recording_btn.setText("Go to Record")
            except (ValueError, TypeError):
                self._recording_pill.set_idle()
                self._recording_btn.setText("Start Recording")
        else:
            self._recording_pill.set_idle()
            self._recording_btn.setText("Start Recording")

    # -------------------------------------------------------------------------
    # Interaction slots
    # -------------------------------------------------------------------------

    @Slot(int)
    def _on_recent_session_clicked(self, row: int) -> None:
        """Handle click on a recent session row — emit signals for cross-view nav."""
        if row < 0:
            return
        item = self._recent_list.item(row)
        if item is None:
            return
        row_widget = self._recent_list.itemWidget(item)
        if row_widget is None:
            return
        session_id = row_widget._session_id
        self.session_selected.emit(session_id)
        self.navigate_requested.emit(1)  # index 1 = Sessions view
