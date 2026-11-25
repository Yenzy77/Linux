#!/usr/bin/env python3
"""Print a proposed Limine header update for a locally generated menu."""
from pathlib import Path
import re
import sys

DIRECTIVES = {
    b"timeout": b"3",
    b"wallpaper": b"boot():/ii-limine-theme/wallpaper.qoi",
    b"wallpaper_style": b"stretched",
    b"term_margin_gradient": b"64",
    b"term_foreground": b"cdd6f4",
    b"term_background": b"ee252535",
    b"term_foreground_bright": b"eef2ff",
    b"term_background_bright": b"ee272737",
    b"interface_help_colour": b"c7d2fe",
    b"interface_help_colour_bright": b"eef2ff",
}
PALETTE = tuple(DIRECTIVES)[4:]


def prepare(data):
    entry = re.search(rb"^[ \t]*/[^/\s]", data, re.MULTILINE)
    if not entry or b"\r" in data:
        raise ValueError("Expected a local LF-terminated menu with boot entries.")
    header, body = data[:entry.start()], data[entry.start():]
    fields = {}
    for match in re.finditer(rb"^[ \t]*([A-Za-z_]+)[ \t]*:[ \t]*([^\n]*)", header, re.M):
        key = match[1].lower().replace(b"interface_help_color", b"interface_help_colour")
        if key in DIRECTIVES:
            if key in fields:
                raise ValueError("The menu has duplicate managed directives.")
            fields[key] = match
        if key in (b"term_font", b"term_font_size", b"term_font_scale", b"term_font_spacing",
                   b"term_margin", b"interface_resolution"):
            raise ValueError("Review existing font, margin or resolution overrides manually.")
    for key, match in sorted(fields.items(), key=lambda item: item[1].start(), reverse=True):
        if key not in PALETTE:
            header = header[:match.start()] + key + b": " + DIRECTIVES[key] + header[match.end():]
    for key in DIRECTIVES:
        if key not in fields:
            header += key + b": " + DIRECTIVES[key] + b"\n"
    return header + body


if __name__ == "__main__":
    try:
        if len(sys.argv) != 2:
            raise ValueError("Usage: prepare-menu.py LOCAL_MENU")
        sys.stdout.buffer.write(prepare(Path(sys.argv[1]).read_bytes()))
    except (OSError, ValueError) as error:
        sys.exit(f"Menu staging stopped: {error}")
