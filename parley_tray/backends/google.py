# Google Translate's free endpoint (the one its own browser extension uses). Text leaves the device.
from urllib.parse import urlencode

from . import EngineError, post

ENDPOINT = "https://clients5.google.com/translate_a/t"
# Keep each request a reasonable size.
BATCH = 4000

TO_GOOGLE = {"he": "iw", "zh-Hant": "zh-TW", "zh": "zh-CN"}
FROM_GOOGLE = {v: k for k, v in TO_GOOGLE.items()}


def _call(texts: list[str], source: str, target: str) -> list:
    url = f"{ENDPOINT}?client=dict-chrome-ex&sl={TO_GOOGLE.get(source, source)}&tl={TO_GOOGLE.get(target, target)}"
    body = urlencode([("q", t) for t in texts]).encode()
    status, data = post(url, body, {"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
                        "Google Translate")
    if status != 200:
        raise EngineError(f"Google Translate refused the request ({status}). Try again in a minute.")
    if not isinstance(data, list):
        raise EngineError("Unexpected answer from Google Translate.")
    return data


def _text_of(item) -> str:
    """Items are "text" for a fixed source language, or ["text", "detected"] for auto."""
    return str(item[0] if isinstance(item, list) else item or "")


def _chunks(text: str) -> list[str]:
    """Whole lines, packed into pieces of at most BATCH characters."""
    out, cur = [], ""
    for line in text.splitlines(keepends=True):
        if cur and len(cur) + len(line) > BATCH:
            out.append(cur)
            cur = ""
        cur += line
    return out + [cur] if cur else out


def translate(text: str, target: str, fallback: str) -> tuple[str, str, str]:
    """Translate text of any language into target, or into fallback when it already is target.

    Returns (translation, source language, language translated into).
    """
    pieces = _chunks(text)
    if not pieces:
        return "", "und", target
    items = _call(pieces, "auto", target)
    first = items[0] if items else None
    source = str(first[1]) if isinstance(first, list) and len(first) > 1 else "und"
    source = FROM_GOOGLE.get(source, source)
    if same_language(source, target) and not same_language(target, fallback):
        items = _call(pieces, source, fallback)
        target = fallback
    return "".join(_text_of(i) for i in items), source, target


def same_language(a: str, b: str) -> bool:
    """By primary subtag, so "zh-Hant" and "zh" count as the same language."""
    return a.lower().split("-")[0] == b.lower().split("-")[0]


if __name__ == "__main__":
    import sys

    print(translate(" ".join(sys.argv[1:]) or "xin chào", "vi", "en"))
