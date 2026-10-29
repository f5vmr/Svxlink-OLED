"""
SvxLink-OLED V0.1
Horizontal text scrolling support.

Hardware-independent scrolling calculations.
"""


def scroll_position(
    text_width,
    display_width,
    elapsed,
    speed=20,
    pause=1.0,
):
    """
    Calculate the horizontal scroll offset.

    Returns zero when the text fits the display.

    Otherwise scrolls from left to right through
    the text, pauses at both ends, and repeats.

    speed is measured in pixels per second.
    """

    overflow = max(0, text_width - display_width)

    if overflow == 0:
        return 0

    travel_time = overflow / speed
    cycle = (pause * 2) + (travel_time * 2)

    position = elapsed % cycle

    if position < pause:
        return 0

    position -= pause

    if position < travel_time:
        return int(position * speed)

    position -= travel_time

    if position < pause:
        return overflow

    position -= pause

    return max(
        0,
        overflow - int(position * speed),
    )
