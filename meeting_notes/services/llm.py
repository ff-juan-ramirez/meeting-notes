"""LLM service: Ollama HTTP API wrapper for note generation."""
import requests
from pathlib import Path

from meeting_notes.core.storage import get_config_dir

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1:8b"
OLLAMA_TIMEOUT = 120  # seconds
TOKEN_CHARS = 4  # chars per token estimate
CHUNK_TOKEN_LIMIT = 6000  # tokens per chunk for map-reduce
MAX_TOKENS_BEFORE_CHUNKING = 8000

BUILTIN_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
USER_TEMPLATES_DIR = get_config_dir() / "templates"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def list_templates() -> list[dict]:
    """Return all templates: built-in + user-created.

    Each dict: {name: str, path: Path, builtin: bool}
    Built-ins are listed first (sorted), then user templates (sorted).
    """
    templates = []
    for p in sorted(BUILTIN_TEMPLATES_DIR.glob("*.txt")):
        templates.append({"name": p.stem, "path": p, "builtin": True})
    USER_TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    for p in sorted(USER_TEMPLATES_DIR.glob("*.txt")):
        templates.append({"name": p.stem, "path": p, "builtin": False})
    return templates


def load_template(template_name: str) -> str:
    """Load template by name. User templates take precedence over built-ins.

    Raises ValueError if template is not found in either location.
    """
    user_path = USER_TEMPLATES_DIR / f"{template_name}.txt"
    if user_path.exists():
        return user_path.read_text()
    builtin_path = BUILTIN_TEMPLATES_DIR / f"{template_name}.txt"
    if builtin_path.exists():
        return builtin_path.read_text()
    raise ValueError(f"Template not found: {template_name}")


def save_template(name: str, content: str) -> Path:
    """Save a user template. Raises ValueError if name collides with a built-in."""
    if (BUILTIN_TEMPLATES_DIR / f"{name}.txt").exists():
        raise ValueError(f"'{name}' is a built-in template. Use a different name.")
    USER_TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    path = USER_TEMPLATES_DIR / f"{name}.txt"
    path.write_text(content)
    return path


def delete_template(name: str) -> None:
    """Delete a user template. Raises ValueError if it's built-in."""
    if (BUILTIN_TEMPLATES_DIR / f"{name}.txt").exists():
        raise ValueError(f"Cannot delete built-in template '{name}'.")
    path = USER_TEMPLATES_DIR / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Template not found: {name}")
    path.unlink()


def duplicate_template(source_name: str, new_name: str) -> Path:
    """Duplicate any template (built-in or user) to a new user template."""
    content = load_template(source_name)
    return save_template(new_name, content)


def estimate_tokens(text: str) -> int:
    """Estimate token count as len(text) // 4 (per D-13)."""
    return len(text) // TOKEN_CHARS


def chunk_transcript(text: str) -> list[str]:
    """Split text into ~6,000-token (~24,000 char) chunks.

    Splits on newline boundary when possible to avoid mid-sentence breaks.
    """
    chunk_chars = CHUNK_TOKEN_LIMIT * TOKEN_CHARS  # 24000
    chunks = []
    while len(text) > chunk_chars:
        split_at = text.rfind("\n", 0, chunk_chars)
        if split_at == -1:
            split_at = chunk_chars
        chunks.append(text[:split_at].strip())
        text = text[split_at:].strip()
    if text:
        chunks.append(text)
    return chunks


def build_prompt(template_text: str, transcript: str) -> str:
    """Build the full prompt by substituting {transcript} in the template."""
    return template_text.replace("{transcript}", transcript)


def generate_notes(prompt: str, timeout: int = OLLAMA_TIMEOUT) -> str:
    """POST to Ollama API and return the response text.

    Raises TimeoutError on timeout (per D-12).
    Raises ConnectionError when Ollama is not running.
    Raises RuntimeError on non-200 response.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
    except requests.exceptions.Timeout:
        raise TimeoutError(
            f"Ollama timed out after {timeout}s. The model may be overloaded — try again or increase timeout."
        )
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Ollama is not running. Run: ollama serve")

    if response.status_code != 200:
        raise RuntimeError(f"Ollama returned HTTP {response.status_code}: {response.text}")

    data = response.json()
    return data["response"]
