"""LLM service: Ollama HTTP API wrapper for note generation."""
import requests
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1:8b"
OLLAMA_TIMEOUT = 120  # seconds
TOKEN_CHARS = 4  # chars per token estimate
CHUNK_TOKEN_LIMIT = 6000  # tokens per chunk for map-reduce
MAX_TOKENS_BEFORE_CHUNKING = 8000

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
VALID_TEMPLATES = ("meeting", "minutes", "1on1")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

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


def load_template(template_name: str) -> str:
    """Load a prompt template file by name.

    Raises ValueError if template_name is not in VALID_TEMPLATES.
    Raises FileNotFoundError if template file is missing.
    """
    if template_name not in VALID_TEMPLATES:
        raise ValueError(f"Invalid template: {template_name}. Must be one of: {', '.join(VALID_TEMPLATES)}")
    template_path = TEMPLATES_DIR / f"{template_name}.txt"
    return template_path.read_text()


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
