import json
import os
from pathlib import Path

import gi

gi.require_version("Secret", "1")
from gi.repository import Secret  # noqa: E402

PATH = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "parley-tray" / "settings.json"


def defaults() -> dict:
    # A Vietnamese speaker at an English-speaking company: read in Vietnamese, write in English.
    return {
        "target": "vi",  # what other languages are translated into
        "fallback": "en",  # what text already in `target` is translated into
        "proofreader": "languagetool",  # or "gemini"
        "gemini_model": "gemini-3.5-flash-lite",
        "shortcuts": False,  # Super+T / Super+G set up once; removing them later is respected
    }


def _stored() -> dict:
    try:
        return json.loads(PATH.read_text())
    except (OSError, ValueError):
        return {}


def load() -> dict:
    return {**defaults(), **_stored()}


# Only what the user changed is stored, so new defaults still reach everything else.
def save(**patch) -> dict:
    stored = {**_stored(), **patch}
    base = defaults()
    stored = {k: v for k, v in stored.items() if base.get(k) != v}
    PATH.parent.mkdir(parents=True, exist_ok=True)
    PATH.write_text(json.dumps(stored, indent=2) + "\n")
    return load()


# The API key lives in the GNOME keyring, not in the settings file.
_SCHEMA = Secret.Schema.new("io.github.tuzkituan.ParleyTray", Secret.SchemaFlags.NONE,
                            {"service": Secret.SchemaAttributeType.STRING})
_ATTRS = {"service": "gemini"}


def gemini_key() -> str:
    try:
        return Secret.password_lookup_sync(_SCHEMA, _ATTRS, None) or ""
    except Exception:
        return ""


def save_gemini_key(key: str) -> None:
    key = key.strip()
    if key:
        Secret.password_store_sync(_SCHEMA, _ATTRS, Secret.COLLECTION_DEFAULT, "Parley Gemini API key", key, None)
    else:
        Secret.password_clear_sync(_SCHEMA, _ATTRS, None)
