# meeting-notes

Local meeting capture, transcription, and Notion notes — 100% offline, no meeting bots.

A CLI tool for macOS + Apple Silicon. Records system audio and microphone simultaneously via
BlackHole + ffmpeg, transcribes locally with mlx-whisper (Whisper large-v3-turbo on MLX),
generates structured meeting notes with Ollama llama3.1:8b, and pushes them to Notion.
No cloud APIs, no data leaving your machine.

---

## Prerequisites

All dependencies must be installed before running `meet init`.

- **macOS with Apple Silicon** (M1/M2/M3/M4) — MLX requires Apple Silicon
- **Python 3.11+** — `brew install python` or use [pyenv](https://github.com/pyenv/pyenv)
- **ffmpeg** — `brew install ffmpeg`
- **BlackHole 2ch** — `brew install blackhole-2ch`
- **Ollama** — `brew install ollama` then pull the model: `ollama pull llama3.1:8b`
- **Notion integration token** — Create one at https://www.notion.so/my-integrations

---

## Audio MIDI Setup

BlackHole must be configured as a Multi-Output Device so system audio goes to both your
speakers and the BlackHole virtual device (for capture). This is a one-time setup.

**Steps:**

1. Open **Audio MIDI Setup** (Spotlight: "Audio MIDI Setup")
2. Click **"+"** at the bottom-left and select **"Create Multi-Output Device"**
3. In the device list, check both **"BlackHole 2ch"** and your speakers/headphones
4. Go to **System Settings > Sound > Output** and select the new **Multi-Output Device**

**Signal routing:**

```
System Audio ──► BlackHole 2ch (device :1) ──┐
                                              ├──► ffmpeg amix ──► recording.wav
MacBook Mic   ────────────────  (device :2) ──┘
```

System audio flows through both BlackHole (for capture) and your speakers (so you still hear
the meeting). The microphone captures your voice. ffmpeg mixes both into a single WAV file.

---

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/meeting-notes.git
cd meeting-notes
pip install .          # or: pip install -e .  (for development)
meet init              # interactive setup wizard
```

---

## Quick Start

```bash
meet init              # first-time setup (device selection, Notion credentials)
meet record            # start recording a meeting
meet stop              # stop recording
meet transcribe        # transcribe the last recording
meet summarize         # generate notes + push to Notion
meet list              # view all recordings
```

---

## Commands

### meet record

Start recording system audio and microphone simultaneously.

```bash
meet record
```

Captures both BlackHole (device :1) and MacBook microphone (device :2) and mixes them into
a WAV file. A session is created in `~/.local/share/meeting-notes/`.

---

### meet stop

Stop the active recording.

```bash
meet stop
```

Sends a graceful stop signal to the recording process, writes final metadata including
`duration_seconds`, and clears the active session state.

---

### meet transcribe

Transcribe the last recording (or a specific session) using mlx-whisper.

```bash
meet transcribe
meet transcribe --session abc123
```

**Flags:**

| Flag | Description |
|------|-------------|
| `--session UUID` | Transcribe a specific session by ID |

Transcription runs locally with mlx-community/whisper-large-v3-turbo. Language is
auto-detected. Output is saved as a `.txt` file alongside the recording.

---

### meet summarize

Generate structured meeting notes from the transcript and push to Notion.

```bash
meet summarize
meet summarize --template 1on1
meet summarize --template minutes --session abc123
```

**Flags:**

| Flag | Description |
|------|-------------|
| `--template meeting\|minutes\|1on1` | Note template to use (default: `meeting`) |
| `--session UUID` | Summarize a specific session by ID |

Uses Ollama llama3.1:8b locally. Notes are saved to `~/.local/share/meeting-notes/notes/`
and pushed to Notion if a token and page ID are configured.

**Templates:**

- `meeting` — General meeting summary with key points, decisions, and next steps
- `minutes` — Formal minutes format with attendees section
- `1on1` — One-on-one format with topics, feedback, and goals

---

### meet list

Show all recordings with their status.

```bash
meet list
meet list --status summarized
meet list --json
```

**Flags:**

| Flag | Description |
|------|-------------|
| `--status STATUS` | Filter by status: `not-transcribed`, `transcribed`, `summarized` |
| `--json` | Output as JSON instead of a Rich table |

---

### meet doctor

Check system prerequisites and report their status.

```bash
meet doctor
meet doctor --verbose
```

**Flags:**

| Flag | Description |
|------|-------------|
| `--verbose` | Show detailed information for each check (versions, paths, device details) |

Validates: Python version, BlackHole at device :1, ffmpeg, mlx-whisper, Whisper model
cache, Ollama running, llama3.1:8b pulled, Notion token (if configured), disk space.

---

### meet init

Interactive setup wizard for first-time configuration.

```bash
meet init
```

Guides you through:
1. Audio device detection — parses avfoundation device list and lets you select BlackHole and mic by number
2. Notion credentials — token validation against the Notion API before writing config
3. Test recording — triggers macOS microphone permission prompt
4. Inline doctor run — validates the full setup before you leave the wizard

If a config already exists, `meet init` prompts whether to reconfigure everything or update specific fields.

---

## Global Flags

Available on all commands:

| Flag | Description |
|------|-------------|
| `--quiet` | Suppress all progress output (for scripting) |
| `--version` | Show version and exit |

---

## Configuration

Config file location: `~/.config/meeting-notes/config.json`

```json
{
  "version": 1,
  "audio": {
    "system_device_index": 1,
    "microphone_device_index": 2
  },
  "whisper": {
    "language": null
  },
  "notion": {
    "token": "ntn_...",
    "parent_page_id": "your-page-id"
  }
}
```

- `audio.system_device_index`: ffmpeg device index for BlackHole 2ch (default: `1`)
- `audio.microphone_device_index`: ffmpeg device index for MacBook microphone (default: `2`)
- `whisper.language`: Language code for transcription (`null` = auto-detect, `"en"`, `"es"`, etc.)
- `notion.token`: Notion integration token from https://www.notion.so/my-integrations
- `notion.parent_page_id`: ID of the Notion page where notes will be created

Data is stored in: `~/.local/share/meeting-notes/` (recordings, transcripts, notes)

Run `meet init` to set up or update this config interactively.

---

## Troubleshooting

**No audio captured / silent recording**
Check Audio MIDI Setup — BlackHole must be checked in the Multi-Output Device and the
Multi-Output Device must be set as system output. Run `meet doctor --verbose` to inspect
device indices.

**ffmpeg not found**
```bash
brew install ffmpeg
```

**BlackHole not at device index 1**
Run `meet doctor --verbose` to see actual device indices, then reconfigure with `meet init`.

**Ollama not running**
```bash
ollama serve    # run in a separate terminal, or configure as a launchd service
```

**llama3.1:8b not found**
```bash
ollama pull llama3.1:8b
```

**Notion token invalid**
Create a new integration at https://www.notion.so/my-integrations and paste the new
`ntn_...` token into `meet init` (choose "update specific fields").

**Empty or garbled transcript**
Check audio routing — system audio must flow through BlackHole to be captured. Verify
the Multi-Output Device is selected as system output, not just BlackHole directly.

**mlx-whisper model not cached (slow first transcription)**
The model downloads automatically on first use. Subsequent transcriptions are fast.
Run `meet doctor --verbose` to see the model cache path and size.

**General diagnostics**
```bash
meet doctor          # summary of all checks
meet doctor --verbose  # detailed check output with versions and paths
```
