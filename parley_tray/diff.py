import difflib
import re

_TOKEN = re.compile(r"\s+|\w+|[^\w\s]")


def changes(before: str, after: str) -> list[tuple[str, bool]]:
    """`after` split into (piece, changed) runs, word by word against `before`."""
    a, b = _TOKEN.findall(before), _TOKEN.findall(after)
    out = []
    for op, _, _, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        piece = "".join(b[j1:j2])
        if piece:
            out.append((piece, op != "equal" and not piece.isspace()))
    return out
