import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

TIMEOUT = 20


class EngineError(Exception):
    """A failure worth showing to the user as is."""


def post(url: str, body: bytes, headers: dict, service: str) -> tuple[int, object]:
    """POST and parse JSON; (status, data). Unreachable hosts raise EngineError."""
    req = Request(url, data=body, headers={"User-Agent": "Mozilla/5.0", **headers})
    try:
        with urlopen(req, timeout=TIMEOUT) as res:
            return res.status, json.load(res)
    except HTTPError as e:
        try:
            data = json.load(e)
        except ValueError:
            data = {}
        return e.code, data
    except (URLError, TimeoutError, OSError):
        raise EngineError(f"Couldn't reach {service}. Check your connection.") from None
