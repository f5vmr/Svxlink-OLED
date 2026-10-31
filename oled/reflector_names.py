"""Resolve local SvxLink reflector hostnames into OLED display names."""

import configparser
from pathlib import Path


SVXLINK_CONF = Path("/etc/svxlink/svxlink.conf")
REFLECTOR_NAMES = Path("/etc/svxlink-oled/reflectors.ini")


def reflector_display_name(
    connection_status,
    svxlink_conf=SVXLINK_CONF,
    names_file=REFLECTOR_NAMES,
):
    """Return a friendly name for a connected local reflector."""

    state = str(connection_status or "").strip()

    if state.lower() != "connected":
        return state or "Not connected"

    config = configparser.ConfigParser(
        interpolation=None,
        strict=False,
    )

    try:
        if not config.read(svxlink_conf):
            return "Connected"

        hosts = config.get(
            "ReflectorLogic",
            "HOSTS",
            fallback="",
        ).strip()

        # Multiple hosts may represent failover configurations.
        # Do not guess which hostname is currently active.
        host_list = [
            h.strip().lower()
            for h in hosts.split(",")
            if h.strip()
        ]

        if len(host_list) != 1:
            return "Connected"

        names = configparser.ConfigParser(
            interpolation=None,
        )

        if not names.read(names_file):
            return "Connected"

        return names.get(
            "reflectors",
            host_list[0],
            fallback="Connected",
        )

    except (
        OSError,
        ValueError,
        configparser.Error,
    ):
        return "Connected"
