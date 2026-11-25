"""Pair the current wallpaper with its authoritative ii Matugen colors."""
import hashlib
import io
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import palette

sys.path.insert(0, "/usr/local/lib/ii-sddm-sync")
from sync import STILLS, VIDEOS, load_json, open_local

SIZE = (1920, 1080)
SOCKET = "/run/ii-limine-wallpaper.sock"


def selection(config):
    settings = load_json(config)
    wallpaper = settings.get("background", {}).get("wallpaperPath")
    if not isinstance(wallpaper, str) or not wallpaper:
        raise ValueError("no wallpaper is selected")
    source = os.path.expanduser(wallpaper)
    demuxer = (STILLS | VIDEOS).get(Path(source).suffix.lower())
    if demuxer is None:
        raise ValueError("unsupported wallpaper type")
    blur = settings.get("lock", {}).get("blur", {})
    radius = blur.get("radius", 100)
    radius = min(max(radius, 0), 100) if type(radius) in (int, float) else 100
    if settings.get("panelFamily") == "waffle" or blur.get("enable", True) is False:
        radius = 0
    return source, demuxer, radius


def render(file, demuxer, radius):
    with os.fdopen(os.dup(file.fileno()), "rb") as media:
        fd = media.fileno()
        res = subprocess.run(
            ["/usr/bin/ffmpeg", "-nostdin", "-loglevel", "error", "-protocol_whitelist", "fd",
             "-f", demuxer, "-fd", str(fd), "-max_pixels", "70000000", "-i", "fd:",
             "-map", "0:v:0", "-frames:v", "1",
             "-vf", "scale=1920:1080:force_original_aspect_ratio=increase:force_divisible_by=2,crop=1920:1080,setsar=1",
             "-f", "rawvideo", "-pix_fmt", "rgb24", "-threads", "1", "pipe:1"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, pass_fds=(fd,),
            timeout=30, check=True,
        )
    if len(res.stdout) != SIZE[0] * SIZE[1] * 3:
        raise ValueError("could not decode one wallpaper frame")
    image = Image.frombytes("RGB", SIZE, res.stdout)
    if radius:
        image = image.filter(ImageFilter.GaussianBlur((radius + 1) / 3.3333))
    image = ImageEnhance.Brightness(image).enhance(0.32)
    encoded = io.BytesIO()
    image.save(encoded, format="QOI")
    return encoded.getvalue()


def exchange(payload):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
        conn.settimeout(30)
        conn.connect(SOCKET)
        conn.sendall(payload)
        conn.shutdown(socket.SHUT_WR)
        with conn.makefile("rb") as response:
            return response.readline(150)


def request(payload, reply_pattern):
    for delay in (0, 0.5, 1.5, 3):
        if delay:
            time.sleep(delay)
        try:
            reply = exchange(payload)
            match = re.fullmatch(reply_pattern, reply)
            if match:
                return match
            raise OSError("publisher did not return the expected acknowledgement")
        except OSError as error:
            last_error = error
    raise last_error


def publish_theme(image, wallpaper_digest, colors):
    color_digest = palette.digest(colors)
    message = f"theme1 {wallpaper_digest} {' '.join(colors)}\n".encode() + image
    request(message, f"ok {wallpaper_digest} {color_digest}\n".encode())


def published_state():
    reply = request(b"state2\n", rb"state ([a-f0-9]{64}|-) ([a-f0-9]{64})\n")
    return reply[1].decode(), reply[2].decode()


def read_record(record):
    try:
        data = load_json(record)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def write_record(record, data):
    with tempfile.NamedTemporaryFile(mode="w", dir=record.parent, delete=False) as temporary:
        pending = Path(temporary.name)
        try:
            json.dump(data, temporary)
            temporary.flush()
            os.replace(pending, record)
        finally:
            pending.unlink(missing_ok=True)


def fingerprint(source, radius, file):
    info = os.fstat(file.fileno())
    return [1, source, radius, info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns]


class PairPending(ValueError):
    pass


def version(path):
    info = path.stat()
    return [info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns]


def inputs(config, state):
    source, demuxer, radius = selection(config)
    with open_local(source) as file:
        current = fingerprint(source, radius, file)
    colors_file = state / "colors.json"
    path_file = state / "wallpaper/path.txt"
    stamps = [version(colors_file), version(path_file)]
    colors = palette.from_matugen(load_json(colors_file))
    with open_local(str(path_file)) as stream:
        generated_from = stream.read(4097).decode().strip()
    if len(generated_from) > 4096 or stamps != [version(colors_file), version(path_file)]:
        raise PairPending("Matugen outputs are still changing")
    thumbnail = load_json(config).get("background", {}).get("thumbnailPath", "")
    accepted = {source}
    if demuxer in VIDEOS.values() and thumbnail:
        accepted.add(os.path.expanduser(thumbnail))
    return source, demuxer, radius, current, colors, stamps, generated_from, accepted


def check_pair(current, stamps, source, accepted, saved):
    old = saved.get("fingerprint", [])
    same_wallpaper = current[:2] == old[:2] and current[3:] == old[3:]
    if source not in accepted and not (source == "" and same_wallpaper):
        raise PairPending("waiting for Matugen's source to match the ii wallpaper")
    previous = saved.get("matugen_stamps")
    if previous and ((stamps[0] != previous[0] and stamps[1] == previous[1])
                     or (not same_wallpaper and stamps[0] == previous[0])):
        raise PairPending("waiting for both Matugen outputs from the wallpaper change")


def sync(config, state, cache, boot_id):
    cache.mkdir(mode=0o700, parents=True, exist_ok=True)
    record = cache / "input.json"
    for _ in range(10):
        try:
            first = inputs(config, state)
            time.sleep(0.3)
            if inputs(config, state) != first:
                continue
            source, demuxer, radius, current, colors, stamps, generated_from, accepted = first
            saved = read_record(record)
            check_pair(current, stamps, generated_from, accepted, saved)
            new_palette = palette.digest(colors)
            digest = saved.get("sha256") if saved.get("fingerprint") == current else None
            if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
                digest = None
            esp = published_state()
            if digest and esp == (digest, new_palette):
                print("Limine wallpaper and palette already match.")
            else:
                image = b""
                if digest is None or esp[0] != digest:
                    with open_local(source) as file:
                        image = render(file, demuxer, radius)
                    digest = hashlib.sha256(image).hexdigest()
                if inputs(config, state) != first:
                    continue
                publish_theme(image, digest, colors)
                print(f"Limine theme acknowledged (wallpaper {digest}, palette {new_palette}).")
            data = {"fingerprint": current, "sha256": digest, "palette_sha256": new_palette,
                    "matugen_stamps": stamps, "boot_id": boot_id}
            if saved != data:
                write_record(record, data)
            # Reconcile changes coalesced by systemd while publication was active.
            time.sleep(0.2)
            if inputs(config, state) == first:
                return
        except (PairPending, FileNotFoundError, json.JSONDecodeError):
            time.sleep(0.25)
        except (ValueError, subprocess.SubprocessError) as error:
            print(f"Limine theme was retained: {error}", file=sys.stderr)
            return
    print("Limine theme retained while waiting for a complete wallpaper and palette pair.")


if __name__ == "__main__":
    home = Path.home()
    config = Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config")
    cache = Path(os.environ.get("CACHE_DIRECTORY") or home / ".cache/ii-limine-wallpaper")
    state = Path(os.environ.get("XDG_STATE_HOME") or home / ".local/state")
    boot_id = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    try:
        sync(config / "illogical-impulse/config.json", state / "quickshell/user/generated", cache, boot_id)
    except OSError as error:
        sys.exit(f"Limine synchronization failed, leaving the last confirmed record intact: {error}")
