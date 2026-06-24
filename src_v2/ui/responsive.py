"""
Shared responsive UI helpers for duplicated src_v2 tool windows.
"""

from typing import Dict

from utils.runtime import get_ui_font_size


def calculate_responsive_font_size(width: int, height: int, base_size: int = 20) -> int:
    """Scale the base font size according to the current window dimensions."""
    default_base = max(18, min(24, get_ui_font_size(default=base_size)))
    base_width = 1366
    base_height = 900
    width_ratio = max(0.80, min(1.10, width / base_width))
    height_ratio = max(0.80, min(1.10, height / base_height))
    ratio = (width_ratio * 0.65) + (height_ratio * 0.35)
    scaled = int(round(default_base * ratio))
    return max(18, min(24, scaled))


def build_scale_tokens(font_size: int) -> Dict[str, int]:
    """Return common typography and control-size tokens for unified v2 tool styling."""
    base = max(18, min(24, font_size))
    small = max(16, base - 2)
    label = max(17, base - 1)
    button = max(17, base - 1)
    control_height = max(38, base + 10)
    button_min_width = max(112, int(base * 4.4))

    return {
        "base": base,
        "small": small,
        "label": label,
        "title": max(24, base + 4),
        "section": max(20, base + 1),
        "button": button,
        "input": max(18, base),
        "mono": max(16, base - 2),
        "padding_x": max(12, int(base * 0.78)),
        "padding_y": max(6, int(base * 0.30)),
        "control_height": control_height,
        "button_min_width": button_min_width,
        "card_radius": max(10, int(base * 0.5)),
        "panel_spacing": max(12, int(base * 0.70)),
    }


# Made with Bob