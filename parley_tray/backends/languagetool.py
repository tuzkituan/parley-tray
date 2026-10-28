# English proofreading through LanguageTool's free public API. Text leaves the device.
import re
from urllib.parse import urlencode

from . import EngineError, post

ENDPOINT = "https://api.languagetool.org/v2/check"
# Style hints and US-vs-UK spelling are opinions, not mistakes.
SKIP_ISSUES = {"style", "locale-violation"}
_STRIP = re.compile(r"^[(\"'`\[{<]+|[)\"'`\]}>,;:!?.]+$")


def _code_spans(text: str) -> list[tuple[int, int]]:
    """Spans of code-like words ("Tour.GuideButton", "PRD", "snake_case", URLs, @mentions)."""
    spans = []
    for m in re.finditer(r"\S+", text):
        word = _STRIP.sub("", m.group())
        if any(c.isupper() for c in word[1:]) or re.search(r"\w[._/\\:#@-]\w", word) or word[:1] in ("@", "#"):
            spans.append((m.start(), m.end()))
    return spans


def _keep(at: int, length: int, issue: str, text: str, code: list[tuple[int, int]]) -> bool:
    """Leave code alone, and capitalized words mid-sentence: they are names, not misspellings."""
    if any(at < b and at + length > a for a, b in code):
        return True
    if issue != "misspelling":
        return False
    return text[at:at + 1].isupper() and not re.search(r"(\A|[.!?]\s+)\Z", text[:at])


def _utf16_index(text: str) -> list[int]:
    """Code point index for each UTF-16 offset: LanguageTool counts like Java strings."""
    out = []
    for i, ch in enumerate(text):
        out.extend([i, i] if ord(ch) > 0xFFFF else [i])
    out.append(len(text))
    return out


def fix(text: str) -> str:
    status, data = post(ENDPOINT, urlencode({"text": text, "language": "en-US"}).encode(),
                        {"Content-Type": "application/x-www-form-urlencoded"}, "LanguageTool")
    if status != 200:
        raise EngineError(f"LanguageTool refused the request ({status}). Try again in a minute.")
    matches = data.get("matches") if isinstance(data, dict) else None
    if not isinstance(matches, list):
        raise EngineError("Unexpected answer from LanguageTool.")

    index = _utf16_index(text)
    code = _code_spans(text)
    edits = []
    for m in matches:
        if not m.get("replacements") or m["rule"]["issueType"] in SKIP_ISSUES:
            continue
        start = index[min(m["offset"], len(index) - 1)]
        end = index[min(m["offset"] + m["length"], len(index) - 1)]
        edits.append((start, end, m["replacements"][0]["value"], m["rule"]["issueType"]))

    # Apply from the end so earlier offsets stay valid; skip overlapping suggestions.
    out = text
    limit = len(text) + 1
    for start, end, value, issue in sorted(edits, reverse=True):
        if end > limit or _keep(start, end - start, issue, text, code):
            continue
        out = out[:start] + value + out[end:]
        limit = start
    return out


if __name__ == "__main__":
    import sys

    print(fix(" ".join(sys.argv[1:]) or "i dont think so, we should of checked teh logs first"))
