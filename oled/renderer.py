"""
SvxLink-OLED V0.1
Hardware-independent monochrome display renderer.

Supports 128x64 and 128x128 OLED resolutions.
"""

from PIL import Image, ImageDraw, ImageFont


def render_status(
    callsign="G4NAB",
    rx=False,
    tx=False,
    talkgroup="Standby",
    width=128,
    height=64,
):
    """Render local SvxLink node status into a monochrome image."""

    if (width, height) not in ((128, 64), (128, 128)):
        raise ValueError("Unsupported OLED resolution")

    image = Image.new("1", (width, height), 0)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    draw.text((2, 2), str(callsign), font=font, fill=1)
    draw.line((0, 17, width - 1, 17), fill=1)

    draw.text(
        (2, 22),
        "RX: ACTIVE" if rx else "RX: IDLE",
        font=font,
        fill=1,
    )

    draw.text(
        (68, 22),
        "TX: ACTIVE" if tx else "TX: IDLE",
        font=font,
        fill=1,
    )

    draw.text(
        (2, 43),
        f"TG: {talkgroup}",
        font=font,
        fill=1,
    )

    return image
