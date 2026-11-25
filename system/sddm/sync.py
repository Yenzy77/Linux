#!/usr/bin/python -I
"""Send selected ii/Matugen data over a local socket and publish it as SDDM INI."""
import json
import math
import os
import re
import socket
import stat
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SOCKET = "/run/ii-sddm-sync.sock"
STATE = Path("/var/lib/ii-sddm-sync")
MAX_HEADER = 16 * 1024
MAX_IMAGE = 10 * 1024 * 1024
MAX_VIDEO = 96 * 1024 * 1024
COLORS = """background error error_container inverse_on_surface inverse_primary inverse_surface
on_background on_error on_error_container on_primary on_primary_container on_primary_fixed
on_primary_fixed_variant on_secondary on_secondary_container on_secondary_fixed
on_secondary_fixed_variant on_surface on_surface_variant on_tertiary on_tertiary_container
on_tertiary_fixed on_tertiary_fixed_variant outline outline_variant primary primary_container
primary_fixed primary_fixed_dim scrim secondary secondary_container secondary_fixed
secondary_fixed_dim shadow surface surface_bright surface_container surface_container_high
surface_container_highest surface_container_low surface_container_lowest surface_dim surface_tint
surface_variant tertiary tertiary_container tertiary_fixed tertiary_fixed_dim""".split()
CLOCK = "background.widgets.clock."
DIGITAL = CLOCK + "digital."
COOKIE = CLOCK + "cookie."
RULES = {
    "panelFamily": ("ii", "waffle"),
    "time.format": str,
    "time.secondPrecision": bool,
    "lock.blur.enable": bool,
    "lock.blur.radius": (0, 100),
    "lock.showLockedText": bool,
    "lock.materialShapeChars": bool,
    CLOCK + "styleLocked": ("none", "digital", "cookie"),
    CLOCK + "quote.text": str,
    CLOCK + "quote.enable": bool,
    DIGITAL + "font.family": str,
    DIGITAL + "font.roundness": (0, 100),
    DIGITAL + "font.size": (10, 250),
    DIGITAL + "font.weight": (1, 1000),
    DIGITAL + "font.width": (25, 200),
    DIGITAL + "showDate": bool,
    DIGITAL + "vertical": bool,
    DIGITAL + "animateChange": bool,
    DIGITAL + "adaptiveAlignment": bool,
    COOKIE + "constantlyRotate": bool,
    COOKIE + "dateStyle": ("hide", "rect", "bubble", "border"),
    COOKIE + "dialNumberStyle": ("full", "dots", "numbers", "none"),
    COOKIE + "hourHandStyle": ("fill", "hollow", "classic", "hide"),
    COOKIE + "hourMarks": bool,
    COOKIE + "minuteHandStyle": ("thin", "medium", "bold", "classic", "hide"),
    COOKIE + "secondHandStyle": ("dot", "classic", "line", "hide"),
    COOKIE + "sides": (3, 64),
    COOKIE + "timeIndicators": bool,
    COOKIE + "useSineCookie": bool,
    "appearance.fonts.main": str,
    "appearance.fonts.expressive": str,
    "appearance.fonts.reading": str,
    "appearance.transparency.enable": bool,
    "appearance.transparency.contentTransparency": (0, 1),
    "appearance.transparency.backgroundTransparency": (0, 1),
}
SETTING_RULES = {"IISetting_" + key.replace(".", "_"): rule for key, rule in RULES.items()}
COLOR_KEYS = {"IIColor_" + key for key in COLORS}
STILLS = {".png": "png_pipe", ".jpg": "jpeg_pipe", ".jpeg": "jpeg_pipe", ".webp": "webp_pipe"}
VIDEOS = {".gif": "gif", ".avi": "avi", ".mp4": "mov", ".mov": "mov", ".m4v": "mov",
          ".mkv": "matroska", ".webm": "matroska"}


def open_local(path):
    if not path.startswith("/") or any(part in ("", ".", "..") for part in path[1:].split("/")):
        raise ValueError("expected an absolute path without traversal")
    *parents, name = path[1:].split("/")
    directory = os.open("/", os.O_DIRECTORY)
    try:
        for part in parents:
            child = os.open(part, os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        stream = os.fdopen(fd, "rb")
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            stream.close()
            raise ValueError("expected a regular file")
        return stream
    finally:
        os.close(directory)


def valid(value, rule):
    if rule is str:
        return type(value) is str and len(value.encode("utf-8")) <= 512 and "\0" not in value
    if rule is bool:
        return type(value) is bool
    if isinstance(rule[0], str):
        return type(value) is str and value in rule
    return type(value) in (float, int) and rule[0] <= value <= rule[1] and math.isfinite(value)


def validate(values):
    if not isinstance(values, dict):
        raise ValueError("invalid settings object")
    for key, value in values.items():
        if key in COLOR_KEYS and type(value) is str and re.fullmatch(r"#[a-fA-F0-9]{6}", value):
            continue
        if key in SETTING_RULES and valid(value, SETTING_RULES[key]):
            continue
        raise ValueError("invalid settings field")


def nested(data, key):
    for component in key.split("."):
        if not isinstance(data, dict):
            return None
        data = data.get(component)
    return data


def config_values(ii, palette):
    values = {f"IIColor_{key}": palette[key] for key in COLORS if key in palette}
    for key, rule in RULES.items():
        value = nested(ii, key)
        if valid(value, rule):
            values["IISetting_" + key.replace(".", "_")] = value
    validate(values)
    if not COLOR_KEYS <= values.keys():
        raise ValueError("Matugen palette is incomplete")
    return values


def render_media(source, dest):
    suffix = Path(source).suffix.lower()
    demuxer = (STILLS | VIDEOS).get(suffix)
    if demuxer is None:
        raise ValueError("unsupported wallpaper format")
    image = dest / "wallpaper.jpg"
    video = dest / "wallpaper.mp4" if suffix in VIDEOS else None
    with open_local(source) as file:
        fd = file.fileno()
        args = ["/usr/bin/ffmpeg", "-nostdin", "-loglevel", "error", "-protocol_whitelist", "fd",
                "-f", demuxer, "-fd", str(fd), "-i", "fd:", "-map", "0:v:0",
                "-map_metadata", "-1", "-map_chapters", "-1", "-an", "-sn", "-dn",
                "-vf", "scale=w='min(iw,2560)':h='min(ih,1440)':"
                       "force_original_aspect_ratio=decrease:force_divisible_by=2,setsar=1", "-threads", "2"]

        def run(options, target):
            file.seek(0)
            subprocess.run(args + options + [str(target)], pass_fds=(fd,), check=True, timeout=100)

        run(["-frames:v", "1", "-c:v", "mjpeg", "-q:v", "3", "-f", "image2", "-update", "1"], image)
        if video:
            run(["-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-pix_fmt", "yuv420p",
                 "-fpsmax", "60", "-movflags", "+faststart", "-fs", str(MAX_VIDEO)], video)
    return image, video


def load_json(path):
    with open_local(str(path)) as file:
        return json.loads(file.read(2 * 1024 * 1024))


def send(config, palette, socket_path=SOCKET):
    ii = load_json(config)
    values = config_values(ii, load_json(palette))
    source = nested(ii, "background.wallpaperPath")
    if type(source) is not str or not source:
        raise ValueError("ii has no wallpaper selected")
    source = os.path.expanduser(source)
    with tempfile.TemporaryDirectory(prefix="ii-sddm-wallpaper-") as directory:
        image, video = render_media(source, Path(directory))
        limits = {"image": image.stat().st_size, "video": video.stat().st_size if video else 0}
        if not 0 < limits["image"] <= MAX_IMAGE or limits["video"] > MAX_VIDEO:
            raise ValueError("wallpaper exceeds the publication size limit")
        header = json.dumps({"values": values, **limits}, ensure_ascii=True).encode() + b"\n"
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as peer:
            peer.settimeout(45)
            peer.connect(socket_path)
            peer.sendall(header)
            for path in (image, video):
                if path:
                    with path.open("rb") as file:
                        peer.sendfile(file)
            peer.shutdown(socket.SHUT_WR)
            with peer.makefile("rb") as response:
                if response.readline(32) != b"ok\n":
                    raise ValueError("the greeter rejected the wallpaper or settings")



def input_version(*paths):
    versions = []
    for path in paths:
        with open_local(str(path)) as stream:
            info = os.fstat(stream.fileno())
        versions.append((info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns))
    return versions


def send_latest(config, palette, socket_path=SOCKET):
    # ii first writes wallpaper settings, then Matugen writes its color output.
    # A path unit can coalesce changes while its oneshot service is active.
    for _ in range(5):
        version = input_version(config, palette)
        time.sleep(0.25)
        if input_version(config, palette) != version:
            continue
        try:
            send(config, palette, socket_path)
        except ValueError:
            if input_version(config, palette) != version:
                continue
            raise
        time.sleep(0.25)
        if input_version(config, palette) == version:
            return
    raise ValueError("wallpaper settings and palette did not settle")


def get_asset(stream, length, target, *, video=False):
    with target.open("xb") as out:
        prefix = stream.read(12 if video else min(3, length))
        if (video and prefix[4:8] != b"ftyp") or (not video and prefix != b"\xff\xd8\xff"):
            raise ValueError("invalid wallpaper media")
        out.write(prefix)
        remaining = length - len(prefix)
        last = prefix[-2:]
        while remaining:
            data = stream.read(min(remaining, 256 * 1024))
            if not data:
                raise ValueError("incomplete wallpaper")
            out.write(data)
            last = (last + data)[-2:]
            remaining -= len(data)
        if not video and last != b"\xff\xd9":
            raise ValueError("incomplete JPEG wallpaper")
        out.flush()
        os.fsync(out.fileno())


def ini_value(key, value):
    if key in COLOR_KEYS:
        return value
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is str:
        return "hex_" + value.encode().hex()
    return str(value)


def publish(stream, state):
    line = stream.readline(MAX_HEADER + 1)
    if len(line) > MAX_HEADER or not line.endswith(b"\n"):
        raise ValueError("invalid publication header")
    header = json.loads(line)
    if not isinstance(header, dict) or header.keys() != {"values", "image", "video"}:
        raise ValueError("invalid publication fields")
    values = header["values"]
    validate(values)
    image, video = header["image"], header["video"]
    if type(image) is not int or not 5 <= image <= MAX_IMAGE:
        raise ValueError("invalid image length")
    if type(video) is not int or (video != 0 and not 12 <= video <= MAX_VIDEO):
        raise ValueError("invalid video length")
    config = state / "theme.conf.user"
    previous = config.read_text() if config.exists() else ""
    slot = "b" if re.search(r"^Background=.*wallpaper-a\.", previous, re.M) else "a"
    still = state / f"wallpaper-{slot}.jpg"
    moving = state / f"wallpaper-{slot}.mp4"
    settings = ["[General]", f"Background={(moving if video else still).as_uri()}"]
    if video:
        settings.append(f"BackgroundPlaceholder={still.as_uri()}")
    settings.extend(f"{key}={ini_value(key, value)}" for key, value in sorted(values.items()))
    with tempfile.TemporaryDirectory(prefix=".sync-", dir=state) as directory:
        stage = Path(directory)
        get_asset(stream, image, stage / still.name)
        if video:
            get_asset(stream, video, stage / moving.name, video=True)
        if stream.read(1):
            raise ValueError("trailing publication data")
        staged_config = stage / config.name
        with staged_config.open("x") as output:
            output.write("\n".join(settings) + "\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(stage / still.name, still)
        if video:
            os.replace(stage / moving.name, moving)
        else:
            moving.unlink(missing_ok=True)
        os.replace(staged_config, config)
        fd = os.open(state, os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def receive():
    with socket.socket(fileno=0) as peer:
        _, uid, _ = struct.unpack("3i", peer.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
        if uid != int(os.environ["II_SDDM_PUBLISHER_UID"]):
            raise PermissionError("unexpected theme publisher uid")
        peer.settimeout(30)
        with peer.makefile("rb") as stream:
            publish(stream, STATE)
        peer.sendall(b"ok\n")


def main():
    action = sys.argv[1:]
    if action == ["receive"]:
        receive()
    elif action == ["send"]:
        home = Path.home()
        config = Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config")
        state = Path(os.environ.get("XDG_STATE_HOME") or home / ".local/state")
        send_latest(config / "illogical-impulse/config.json", state / "quickshell/user/generated/colors.json")
    else:
        raise ValueError("expected send or receive")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        sys.exit(f"ii-sddm-sync: {exc}")
