"""
SvxLink-OLED V0.1
Hardware-independent monochrome display renderer.

Supports 128x64 and 128x128 OLED resolutions.
"""

from PIL import Image, ImageDraw, ImageFont
from oled.scroll import scroll_position

def render_status(
    callsign="MB5HT",
    reflector="Not connected",
    rx=False,
    tx=False,
    talkgroup="Standby",
    width=128,
    height=64,
    elapsed=0.0,
):
    """Render local SvxLink node status into a monochrome image."""

    if (width, height) not in ((128, 64), (128, 128)):
        raise ValueError("Unsupported OLED resolution")

    image = Image.new("1", (width, height), 0)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    # Node callsign left justified.
    draw.text((2, 2), str(callsign), font=font, fill=1)

    # Reflector right justified on the same line.
    reflector_text = str(reflector)

    available_width = width - 4
    callsign_width = draw.textlength(str(callsign), font=font)
    reflector_width = draw.textlength(reflector_text, font=font)

    # Leave at least four pixels between the two fields.
    while (
        reflector_text
        and callsign_width + reflector_width + 4 > available_width
    ):
        reflector_text = reflector_text[:-1]
        reflector_width = draw.textlength(
            reflector_text,
            font=font,
        )

    reflector_x = width - reflector_width - 2

    draw.text(
        (reflector_x, 2),
        reflector_text,
        font=font,
        fill=1,
    )
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

    # Draw the talkgroup within a clipped scrolling region.
    # Callsign and RX/TX fields remain stationary.

    tg_text = f"TG: {talkgroup}"
    region_width = width - 4

    tg_layer = Image.new("1", (region_width, 14), 0)
    tg_draw = ImageDraw.Draw(tg_layer)

    text_width = tg_draw.textlength(tg_text, font=font)

    offset = scroll_position(
        text_width=text_width,
        display_width=region_width,
        elapsed=elapsed,
    )

    tg_draw.text(
        (-offset, 0),
        tg_text,
        font=font,
        fill=1,
    )

    image.paste(tg_layer, (2, 43))

    return image
