"""
SvxLink-OLED V0.1
Live graphical OLED simulator using Tkinter.

Displays live status from SvxLink-Dash.
No physical OLED hardware required.
"""

import tkinter as tk
import time
from PIL import Image, ImageTk

from oled.renderer import render_status
from oled.status_source import get_oled_status


SCALE = 3
POLL_INTERVAL_MS = 100
WIDTH = 128
HEIGHT = 64


class OLEDWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("SvxLink-OLED V0.1 — Live Simulator")
        self.root.resizable(False, False)

        self.previous_status = None
        self.photo = None
        self.scroll_start = time.monotonic()

        self.display = tk.Label(
            root,
            background="black",
            borderwidth=8,
            relief="ridge",
        )
        self.display.pack(padx=12, pady=12)

        self.connection_label = tk.Label(
            root,
            text="Connecting to MB5HT...",
            font=("Arial", 11),
        )
        self.connection_label.pack(pady=(0, 10))

        self.update_display()

    def update_display(self):
        try:
            status = get_oled_status(timeout=2)
        except (RuntimeError, TimeoutError, ValueError):
            status = {
                "callsign": "MB5HT",
                "rx": False,
                "tx": False,
                "talkgroup": "Offline",
                "online": False,
                "reflector": "Offline",
            }

        if status != self.previous_status:
            if (
                self.previous_status is None
                or status["talkgroup"] != self.previous_status["talkgroup"]
            ):
                self.scroll_start = time.monotonic()

        if True:
            image = render_status(
                callsign=status["callsign"],
                rx=status["rx"],
                tx=status["tx"],
                talkgroup=status["talkgroup"],
                width=WIDTH,
                height=HEIGHT,
                elapsed=time.monotonic() - self.scroll_start,
                reflector=status["reflector"]
            )

            enlarged = image.convert("RGB").resize(
                (WIDTH * SCALE, HEIGHT * SCALE),
                resample=Image.Resampling.NEAREST,
            )

            self.photo = ImageTk.PhotoImage(enlarged)
            self.display.configure(image=self.photo)

            self.connection_label.configure(
                text=(
                    f"{status['callsign']} — "
                    f"{'ONLINE' if status['online'] else 'OFFLINE'}"
                )
            )

            self.previous_status = status

        self.root.after(POLL_INTERVAL_MS, self.update_display)


def main():
    root = tk.Tk()
    OLEDWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
