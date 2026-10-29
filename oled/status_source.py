"""
SvxLink-OLED V0.1
Read-only local status source.

Fetches the established SvxLink-Dash status API and reduces it
to the fields required by the OLED display.
"""

import json
from urllib.request import urlopen
from urllib.error import URLError, HTTPError


DEFAULT_STATUS_URL = "http://192.168.1.214:5000/api/status"


def fetch_status(status_url=DEFAULT_STATUS_URL, timeout=5):
    """
    Fetch the live SvxLink-Dash API response.

    Returns the decoded JSON document.
    Raises RuntimeError if the node cannot be reached
    or the response is invalid.
    """
    try:
        with urlopen(status_url, timeout=timeout) as response:
            data = response.read().decode("utf-8")
    except (URLError, HTTPError) as exc:
        raise RuntimeError(
            f"Unable to fetch SvxLink status from {status_url}"
        ) from exc

    try:
        return json.loads(data)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Invalid JSON returned by SvxLink-Dash") from exc


def get_oled_status(status_url=DEFAULT_STATUS_URL, timeout=5):
    """
    Return only the OLED-relevant fields.

    The result is deliberately small and stable so that the
    renderer does not depend on the full dashboard response.
    """
    payload = fetch_status(status_url=status_url, timeout=timeout)

    status = payload.get("status", {})
    radio_state = status.get("radio_state", {})

    return {
        "callsign": status.get("callsign", "Unknown"),
        "rx": bool(radio_state.get("rx", False)),
        "tx": bool(radio_state.get("tx", False)),
        "talkgroup": status.get("active_talkgroup", "Standby"),
        "online": True,
    }
