#!/usr/bin/env python3
"""Preview, apply, and restore the Phase 1 user overlay without privileges."""
import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

PROFILE = Path(__file__).resolve().parent
PATCH = PROFILE / "profile.patch"
SETTINGS = "illogical-impulse/config.json"
TOOLKIT = {"gtk-3.0/settings.ini", "kdeglobals"}
UPSTREAM = "d192a25faa11cf1d56c839c344c9ef8dd6c2c69d"


def update_map(base, overlay):
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            update_map(base[key], value)
        else:
            base[key] = value


def update_ini(source, changes):
    # Preserve comments and unknown KDE groups and keys.
    lines = source.splitlines(keepends=True)
    for group, options in changes.items():
        found = [i for i, line in enumerate(lines) if line.strip() == f"[{group}]"]
        if len(found) > 1:
            raise ValueError(f"duplicate settings group {group}")
        if not found:
            if lines and not lines[-1].endswith("\n"):
                lines[-1] += "\n"
            lines.extend([f"[{group}]\n", *(f"{key}={value}\n" for key, value in options.items())])
            continue
        first = found[0] + 1
        last = next((i for i in range(first, len(lines)) if lines[i].lstrip().startswith("[")), len(lines))
        for key, value in options.items():
            pattern = re.compile(rf"^[ \t]*{re.escape(key)}[ \t]*=")
            matches = [i for i in range(first, last) if pattern.match(lines[i])]
            if len(matches) > 1:
                raise ValueError(f"duplicate settings key {key} in {group}")
            if matches:
                lines[matches[0]] = f"{key}={value}\n"
            else:
                if last and not lines[last-1].endswith("\n"):
                    lines[last-1] += "\n"
                lines.insert(last, f"{key}={value}\n")
                last += 1
    return "".join(lines)


def config_path(root, name):
    path = root
    for part in Path(name).parts:
        path = path / part
        if path.is_symlink():
            raise ValueError(f"refusing symlink at {path}")
    if path.exists() and (not path.is_file() or path.stat().st_uid != os.getuid()):
        raise ValueError(f"expected a user-owned regular file at {path}")
    return path


def digest(data):
    return None if data is None else hashlib.sha256(data).hexdigest()


def replace(path, data, mode):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".desktop-overlay-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            os.fchmod(stream.fileno(), mode)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def patch_into(root, workspace, names):
    for name in names:
        source = config_path(root, name)
        if not source.is_file():
            raise ValueError(f"Missing {name}. Install the pinned upstream profile first.")
        target = workspace / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    for name in names:
        command = ["git", "apply", "--whitespace=nowarn", f"--include={name}", str(PATCH)]
        check = subprocess.run(command[:2] + ["--check", "--reverse"] + command[2:],
                               cwd=workspace, capture_output=True)
        if check.returncode:
            subprocess.run(command, cwd=workspace, check=True)
    return {name: (workspace / name).read_bytes() for name in names}


def restore(root, backup, allowlist, replace_changed=False):
    index = json.loads((backup / "index.json").read_text())
    if not index or not set(index) <= allowlist:
        raise ValueError("invalid desktop overlay backup index")
    restore_files = []
    for name, info in index.items():
        target = config_path(root, name)
        current = target.read_bytes() if target.exists() else None
        if not replace_changed and digest(current) != info["installed"]:
            raise ValueError(f"current {name} was changed after this overlay")
        data = None if info["previous"] is None else config_path(backup, f"files/{name}").read_bytes()
        if digest(data) != info["previous"]:
            raise ValueError(f"backup digest mismatch for {name}")
        restore_files.append((target, data, info["mode"]))
    for target, data, mode in restore_files:
        if data is None:
            target.unlink(missing_ok=True)
        else:
            replace(target, data, mode)
        print(f"Restored {target.relative_to(root)}")


def make_backup(parent, pending):
    parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    metadata = parent.lstat()
    if (parent.resolve() != parent.absolute()
            or not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != os.getuid()
            or stat.S_IMODE(metadata.st_mode) != 0o700):
        raise ValueError("backup parent must be a private, user-owned directory without symlinks")
    backup = Path(tempfile.mkdtemp(prefix="backup-", dir=parent))
    index = {}
    for name, (updated, previous, mode) in pending.items():
        if previous is not None:
            replace(backup / "files" / name, previous, mode)
        index[name] = {"previous": digest(previous), "installed": digest(updated), "mode": mode}
    replace(backup / "index.json", (json.dumps(index, indent=2) + "\n").encode(), 0o600)
    print(f"Backup saved to {backup}", flush=True)


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-root", type=Path, default=Path.home() / ".config")
    parser.add_argument("--backup-parent", type=Path,
                        default=Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "desktop-baseline")
    parser.add_argument("--upstream", type=Path, help="verify the expected revision in an upstream checkout")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="write the reviewed overlay after taking a backup")
    mode.add_argument("--restore", type=Path, help="restore a backup generated by this script")
    mode.add_argument("--backup", action="store_true", help="back up allowlisted profile files only")
    parser.add_argument("--replace-changed", action="store_true",
                        help="explicitly allow restore to replace files edited since the backup")
    args = parser.parse_args()
    if args.replace_changed and not args.restore:
        parser.error("--replace-changed requires --restore")
    if os.geteuid() == 0:
        parser.error("run the user overlay without sudo")
    root = args.config_root.absolute()
    if not root.is_dir() or root.resolve() != root or root.stat().st_uid != os.getuid():
        parser.error("the configuration root must be a user-owned directory with no symlink components")
    if args.upstream:
        revision = subprocess.check_output(["git", "-C", str(args.upstream), "rev-parse", "HEAD"], text=True).strip()
        if revision != UPSTREAM:
            parser.error(f"expected upstream revision {UPSTREAM}")
    stat_lines = subprocess.check_output(["git", "apply", "--numstat", str(PATCH)], text=True).splitlines()
    names = {line.split("\t")[2] for line in stat_lines}
    if not names or any(part in ("", ".", "..") for name in names for part in name.split("/")):
        raise ValueError("invalid desktop patch paths")
    allowlist = names | TOOLKIT | {SETTINGS}
    if args.restore:
        restore(root, args.restore.absolute(), allowlist, args.replace_changed)
        return
    if args.backup:
        captured = {}
        for name in sorted(allowlist):
            target = config_path(root, name)
            previous = target.read_bytes() if target.exists() else None
            mode = stat.S_IMODE(target.stat().st_mode) if previous is not None else 0o600
            captured[name] = (previous, previous, mode)
        make_backup(args.backup_parent, captured)
        return
    with tempfile.TemporaryDirectory(prefix="desktop-overlay-") as temporary:
        proposed = patch_into(root, Path(temporary), names)
    settings = config_path(root, SETTINGS)
    current = json.loads(settings.read_text()) if settings.exists() else {}
    update_map(current, json.loads((PROFILE / "ii-settings.json").read_text()))
    proposed[SETTINGS] = (json.dumps(current, ensure_ascii=False, indent=2) + "\n").encode()
    for name, changes in json.loads((PROFILE / "toolkit-settings.json").read_text()).items():
        if name not in TOOLKIT:
            raise ValueError("unrecognized toolkit destination")
        target = config_path(root, name)
        proposed[name] = update_ini(target.read_text() if target.exists() else "", changes).encode()

    pending = {}
    for name, data in sorted(proposed.items()):
        target = config_path(root, name)
        previous = target.read_bytes() if target.exists() else None
        if previous != data:
            pending[name] = (data, previous, stat.S_IMODE(target.stat().st_mode) if target.exists() else 0o600)
            print(f"Would {'create' if previous is None else 'update'} {name}")
    if not pending:
        print("The desktop overlay is already present.")
    if not args.apply or not pending:
        return
    make_backup(args.backup_parent, pending)
    installed = []
    try:
        for name, (updated, previous, mode) in pending.items():
            target = config_path(root, name)
            current = target.read_bytes() if target.exists() else None
            if current != previous:
                raise ValueError(f"{name} changed during preflight")
            replace(target, updated, mode)
            installed.append((target, previous, mode))
    except (OSError, ValueError):
        for target, previous, mode in reversed(installed):
            if previous is None:
                target.unlink()
            else:
                replace(target, previous, mode)
        raise


if __name__ == "__main__":
    try:
        run()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        raise SystemExit(f"Desktop overlay preflight or operation failed: {error}") from None
