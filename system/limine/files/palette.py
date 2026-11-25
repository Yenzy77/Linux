"""The six Limine menu colors this integration is allowed to change."""
import hashlib
import re

KEYS = (
    b"term_foreground", b"term_background", b"term_foreground_bright",
    b"term_background_bright", b"interface_help_colour", b"interface_help_colour_bright",
)
COLOR_LINE = re.compile(
    rb"^[ \t]*(" + b"|".join(KEYS) +
    rb"|interface_help_color(?:_bright)?)[ \t]*:[ \t]*([^\r\n]*)",
    re.MULTILINE | re.IGNORECASE,
)
WALLPAPER_MAX = "525252"


def contrast(a, b):
    def luminance(rgb):
        channels = [int(rgb[i:i+2], 16) / 255 for i in (0, 2, 4)]
        linear = [x / 12.92 if x <= .04045 else ((x + .055) / 1.055)**2.4 for x in channels]
        return sum(x * weight for x, weight in zip(linear, (.2126, .7152, .0722)))
    dark, light = sorted((luminance(a), luminance(b)))
    return (light + .05) / (dark + .05)


def from_matugen(roles):
    def role(name):
        value = roles.get(name) if isinstance(roles, dict) else None
        if not isinstance(value, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
            raise ValueError(f"invalid Matugen role {name}")
        return value[1:].lower()

    def readable(hex_color):
        color = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
        for blend in range(21):
            candidate = "".join(f"{round(x + (255-x)*blend/20):02x}" for x in color)
            if contrast(candidate, WALLPAPER_MAX) >= 4.5:
                return candidate
        raise ValueError("could not choose a readable Matugen color")

    def darken(hex_color):
        rgb = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
        scale = min(1, 82 / max(1, *rgb))
        return "ee" + "".join(f"{int(x*scale):02x}" for x in rgb)

    primary, on_primary = role("primary"), role("on_primary")
    return (readable(primary), darken(on_primary), readable(role("on_surface")),
            darken(role("on_surface_variant")), readable(role("secondary")), readable(primary))


def validate_colors(colors):
    if len(colors) != len(KEYS):
        raise ValueError("wrong menu color count")
    for index, value in enumerate(colors):
        is_background = index in (1, 3)
        pattern = r"ee[0-9a-f]{6}" if is_background else r"[0-9a-f]{6}"
        if not isinstance(value, str) or not re.fullmatch(pattern, value):
            raise ValueError("invalid color token")
        if is_background and any(int(value[i:i+2], 16) > 82 for i in (2, 4, 6)):
            raise ValueError("reverse-video text tint is too bright")
        if not is_background and contrast(value, WALLPAPER_MAX) < 4.5:
            raise ValueError("menu text contrast is below 4.5:1")


def header_colors(config):
    entry = re.search(rb"^[ \t]*/[^/\s]", config, re.MULTILINE)
    if entry is None:
        raise ValueError("no Limine entry boundary")
    header, body = config[:entry.start()], config[entry.start():]
    fields = {}
    for match in COLOR_LINE.finditer(header):
        key = match[1].lower().replace(b"interface_help_color", b"interface_help_colour")
        if key in fields:
            raise ValueError("duplicate menu color directive")
        value = match[2].strip()
        width = 8 if b"background" in key else 6
        if not re.fullmatch(rb"[0-9a-fA-F]{%d}" % width, value):
            raise ValueError("unrecognized menu color directive")
        fields[key] = value.decode().lower()
    if fields.keys() != set(KEYS):
        raise ValueError("unexpected Limine color directives")
    return header, body, tuple(fields[key] for key in KEYS)


def config_colors(config):
    return header_colors(config)[2]


def patch_config(config, colors):
    validate_colors(colors)
    header, body, old = header_colors(config)
    if old == colors:
        return config
    values = dict(zip(KEYS, colors))

    def replace(match):
        key = match[1].lower().replace(b"interface_help_color", b"interface_help_colour")
        if match[2].strip().lower() == values[key].encode():
            return match[0]
        return match[0][:match.start(2) - match.start()] + values[key].encode()

    return COLOR_LINE.sub(replace, header) + body


def digest(colors):
    return hashlib.sha256(" ".join(colors).encode()).hexdigest()
