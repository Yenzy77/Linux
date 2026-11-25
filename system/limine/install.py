#!/usr/bin/env python3
"""Stage and install the reviewed Limine synchronization files on CachyOS."""
import argparse
import grp
import os
from pathlib import Path
import pwd
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent / "files"))
from palette import header_colors

HERE = Path(__file__).resolve().parent
LIB = Path("/usr/local/lib/ii-limine-wallpaper")
SYSTEM = Path("/etc/systemd/system")
USER = Path("/etc/systemd/user")
SUDO = ("/usr/bin/sudo", "--")
FILES = {
    "publish.py.in": LIB / "publish.py",
    "render.py": LIB / "render.py",
    "palette.py": LIB / "palette.py",
    "ii-limine-wallpaper.socket.in": SYSTEM / "ii-limine-wallpaper.socket",
    "ii-limine-wallpaper@.service.in": SYSTEM / "ii-limine-wallpaper@.service",
    "ii-limine-wallpaper.socket.d/10-boot-lock.conf":
        SYSTEM / "ii-limine-wallpaper.socket.d/10-boot-lock.conf",
    "ii-limine-render.path": USER / "ii-limine-render.path",
    "ii-limine-render.service": USER / "ii-limine-render.service",
    "ii-limine-boot-lock.conf": Path("/etc/tmpfiles.d/ii-limine-boot-lock.conf"),
}
ASSET = "ii-limine-theme/wallpaper.qoi"
GUID = "8be4df61-93ca-11d2-aa0d-00e098032b8c"


def run(*args, priv=False, capture=False, check=True):
    return subprocess.run(
        (*SUDO, *args) if priv else args, check=check, capture_output=capture,
    )


def fields(account, mount):
    if not re.fullmatch(r"[a-z_][a-z0-9_-]*", account):
        raise ValueError("Specify a conventional local login name.")
    entry = pwd.getpwnam(account)
    group = grp.getgrgid(entry.pw_gid).gr_name
    if entry.pw_uid == 0 or not re.fullmatch(r"[a-z_][a-z0-9_-]*", group):
        raise ValueError("Specify an unprivileged login with a conventional local group.")
    esp = Path(mount)
    if str(esp) != mount or not re.fullmatch(r"(?:/[A-Za-z0-9_.-]+)+", mount) or ".." in esp.parts:
        raise ValueError("Specify the absolute ESP mount point with no shell or systemd escapes.")
    machine_id = Path("/etc/machine-id").read_text().strip()
    if not re.fullmatch(r"[a-f0-9]{32}", machine_id):
        raise ValueError("The host must have an initialized systemd machine ID.")
    return {"@ESP@": mount, "@UID@": str(entry.pw_uid), "@USER@": account,
            "@GROUP@": group, "@MACHINE_ID@": machine_id}


def materialize(source, replacements):
    result = (HERE / "files" / source).read_text()
    if source.endswith(".in"):
        for marker, value in replacements.items():
            result = result.replace(marker, value)
        if re.search(r"@[A-Z_]+@", result):
            raise ValueError("An unresolved host setting remains in a template.")
    return result


def preflight(esp, *, require_header):
    os_release = Path("/etc/os-release").read_text()
    if not re.search(r'^ID="?cachyos"?$', os_release, re.MULTILINE):
        raise ValueError("This baseline targets CachyOS.")
    if esp.resolve() != esp or not esp.is_mount():
        raise ValueError("The ESP must be a mounted canonical directory.")
    mount_type = run("/usr/bin/findmnt", "-nro", "FSTYPE", "--mountpoint", str(esp),
                     capture=True).stdout.strip()
    if mount_type != b"vfat":
        raise ValueError("The ESP is not a mounted FAT filesystem.")
    owner, mode = run("/usr/bin/stat", "-c", "%u %a", str(esp),
                      priv=True, capture=True).stdout.split()
    if owner != b"0" or int(mode, 8) & 0o022:
        raise ValueError("The publisher requires a root-owned ESP without group or other writes.")
    asset_dir = esp / Path(ASSET).parent
    if run("/usr/bin/test", "-L", str(asset_dir), priv=True, check=False).returncode == 0:
        raise ValueError("The managed asset directory cannot be a symlink.")
    secure_boot = Path("/sys/firmware/efi/efivars") / f"SecureBoot-{GUID}"
    if run("/usr/bin/cat", str(secure_boot), priv=True, capture=True).stdout[4:] != b"\0":
        raise ValueError("This publisher requires the existing inactive Secure Boot state.")
    run("/usr/bin/cmp", "-s", str(esp / "EFI/limine/limine_x64.efi"),
        "/usr/share/limine/BOOTX64.EFI", priv=True)
    for line in Path("/etc/default/limine").read_text().splitlines():
        key, _, value = line.partition("=")
        if key.strip() == "ENABLE_ENROLL_LIMINE_CONFIG" and value.split("#", 1)[0].strip().strip("\"'") not in ("", "no"):
            raise ValueError("This publisher requires the existing unenrolled menu.")
    if require_header:
        menu = run("/usr/bin/cat", str(esp / "limine.conf"), priv=True, capture=True).stdout
        header, _, _ = header_colors(menu)
        if any(line not in header.splitlines() for line in (
            b"wallpaper: boot():/ii-limine-theme/wallpaper.qoi",
            b"wallpaper_style: stretched", b"term_margin_gradient: 64", b"timeout: 3",
        )):
            raise ValueError("Prepare the visual header on the local menu first. See this module's README.")
    sync = Path("/usr/local/lib/ii-sddm-sync/sync.py")
    if not sync.is_file():
        raise ValueError("Install the reviewed SDDM synchronization helper first.")
    for dependency in ("/usr/bin/ffmpeg", "/usr/bin/systemd-analyze"):
        if not Path(dependency).is_file():
            raise ValueError(f"Required executable missing: {dependency}")
    from PIL import Image
    Image.init()
    if "QOI" not in Image.SAVE:
        raise ValueError("The installed Pillow needs QOI encoding support.")


def install(rendered, esp):
    changed = []
    for source, dest in rendered.items():
        if run("/usr/bin/test", "-L", str(dest), priv=True, check=False).returncode == 0:
            raise ValueError(f"Refusing to replace symlink: {dest}")
        if run("/usr/bin/cmp", "-s", str(source), str(dest), priv=True, check=False).returncode:
            changed.append((source, dest))
    if not changed:
        print("Installed files already match the selected host settings.")
    else:
        if run("/usr/bin/systemctl", "is-active", "--quiet", "ii-limine-wallpaper.socket",
               "ii-limine-wallpaper@*.service", check=False).returncode == 0:
            raise ValueError("Stop the Limine socket and publisher instances before replacing files.")
        backup = Path(run(
            "/usr/bin/mktemp", "-d", "/root/ii-limine-baseline.XXXXXXXX",
            priv=True, capture=True,
        ).stdout.decode().strip())
        print(f"Permission-preserving backup directory {backup}", flush=True)
        manifest = []
        for _, dest in changed:
            was_present = run("/usr/bin/test", "-e", str(dest), priv=True, check=False).returncode == 0
            manifest.append(f"{'present' if was_present else 'absent'} {dest}\n")
            if was_present:
                saved = backup / dest.relative_to("/")
                run("/usr/bin/install", "-d", "-m", "0700", str(saved.parent), priv=True)
                run("/usr/bin/cp", "-a", "--", str(dest), str(saved), priv=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8") as source:
            source.writelines(manifest)
            source.flush()
            run("/usr/bin/install", "-m", "0600", source.name, str(backup / "manifest"), priv=True)
        for source, dest in changed:
            if not dest.parent.is_dir():
                run("/usr/bin/install", "-d", "-m", "0755", str(dest.parent), priv=True)
            run("/usr/bin/install", "-m", "0644", str(source), str(dest), priv=True)
    asset_dir = esp / Path(ASSET).parent
    if run("/usr/bin/test", "-d", str(asset_dir), priv=True, check=False).returncode:
        run("/usr/bin/mkdir", "-m", "0700", str(asset_dir), priv=True)
    print("The README describes activation after reviewing the installed unit files.")


def main():
    if os.geteuid() == 0:
        raise ValueError("Run the installer as a local user. It requests sudo for individual file operations.")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "preflight", "install"), default="plan", nargs="?")
    parser.add_argument("--user", required=True)
    parser.add_argument("--esp", required=True)
    args = parser.parse_args()
    replacements = fields(args.user, args.esp)
    with tempfile.TemporaryDirectory(prefix="ii-limine-install-") as temporary:
        rendered = {}
        for source, dest in FILES.items():
            staged = Path(temporary) / Path(source.removesuffix(".in"))
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_text(materialize(source, replacements))
            if dest.suffix == ".py":
                compile(staged.read_bytes(), staged.name, "exec")
            rendered[staged] = dest
        if args.mode == "plan":
            for dest in rendered.values():
                print(dest)
            return
        preflight(Path(args.esp), require_header=args.mode == "install")
        if args.mode == "install":
            install(rendered, Path(args.esp))
        else:
            print("Preflight passed for the existing host menu and package EFI.")


if __name__ == "__main__":
    try:
        main()
    except (KeyError, OSError, ValueError, subprocess.CalledProcessError) as error:
        sys.exit(f"Limine setup stopped: {error}")
