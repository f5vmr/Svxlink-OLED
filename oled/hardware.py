"""SvxLink-OLED physical device process. No control endpoints; local status only."""
import configparser
import os
import time
from pathlib import Path

from oled.renderer import render_status
from oled.status_source import get_oled_status

ALLOWED_CONTROLLERS = {"ssd1315", "ssd1306", "sh1106", "sh1107"}
CONFIG = Path(os.environ.get("SVXLINK_OLED_CONFIG", "/etc/svxlink-oled/oled.ini"))


def config_values():
    cfg = configparser.ConfigParser()
    if not cfg.read(CONFIG):
        raise RuntimeError(f"Missing OLED configuration: {CONFIG}")
    p = cfg["oled"]
    controller = p.get("controller", "ssd1315").lower()
    width, height = p.getint("width", 128), p.getint("height", 64)
    if controller not in ALLOWED_CONTROLLERS:
        raise ValueError(f"Unsupported OLED controller: {controller}")
    supported_sizes = {
        "ssd1315": {(128, 64)},
        "ssd1306": {(128, 64)},
        "sh1106": {(128, 64)},
        "sh1107": {(128, 64), (128, 128)},
    }

    if (width, height) not in supported_sizes[controller]:
        raise ValueError(
            f"Unsupported resolution {width}x{height} "
            f"for controller {controller}"
        )
    if p.get("interface", "i2c").lower() != "i2c":
        raise ValueError("Only I2C is supported")
    address = int(p.get("address", "0x3c"), 0)
    if not 0x03 <= address <= 0x77:
        raise ValueError("Invalid 7-bit I2C address")
    # Production endpoint must always be loopback. No remote-node monitoring.
    from urllib.parse import urlsplit
    url = p.get("status_url", "http://127.0.0.1/api/status")
    parsed = urlsplit(url)
    if parsed.scheme != "http" or parsed.hostname not in ("127.0.0.1", "localhost", "::1") or parsed.path != "/api/status" or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Hardware status_url must be local /api/status")
    return dict(controller=controller, width=width, height=height,
                address=address, bus=p.getint("bus", 1), url=url,
                poll=max(0.5, p.getfloat("poll_seconds", 1.0)),
                fps=min(20, max(1, p.getint("scroll_frames_per_second", 10))))


def main():
    cfg = config_values()
    from luma.core.interface.serial import i2c
    from luma import oled as oled_package
    from luma.oled import device as oled_devices
    import importlib.metadata

    version = importlib.metadata.version("luma.oled")
    if cfg["controller"] == "ssd1315" and not hasattr(oled_devices, "ssd1315"):
        raise RuntimeError(f"luma.oled {version} lacks SSD1315; requires 3.15+")
    serial = i2c(port=cfg["bus"], address=cfg["address"])
    device = getattr(oled_devices, cfg["controller"])(serial,
        width=cfg["width"], height=cfg["height"])
    previous = None
    scroll_started = time.monotonic()
    last_poll = 0.0
    last_image = None
    while True:
        now = time.monotonic()
        if previous is None or now - last_poll >= cfg["poll"]:
            last_poll = now
            try:
                status = get_oled_status(status_url=cfg["url"], timeout=2)
            except (RuntimeError, OSError, ValueError) as exc:
                print(f"Local status unavailable: {exc}", flush=True)
                status = {"callsign": "SVXLINK", "reflector": "OFFLINE",
                          "rx": False, "tx": False, "talkgroup": "Offline", "online": False}
            if previous is None or status.get("talkgroup") != previous.get("talkgroup"):
                scroll_started = now
            previous = status
        image = render_status(
            callsign=previous["callsign"], reflector=previous["reflector"],
            rx=previous["rx"], tx=previous["tx"], talkgroup=previous["talkgroup"],
            width=cfg["width"], height=cfg["height"], elapsed=now - scroll_started)
        # Avoid writes when buffer is unchanged.
        if last_image is None or image.tobytes() != last_image:
            try:
                device.display(image)
            except OSError as exc:
                raise RuntimeError(
                    f"OLED I2C display failure on bus "
                    f"{cfg['bus']}, address 0x{cfg['address']:02x}: {exc}"
                ) from exc

            last_image = image.tobytes()
        time.sleep(1.0 / cfg["fps"])


if __name__ == "__main__":
    main()
