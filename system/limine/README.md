# Limine integration

The baseline uses Limine 12.9.6, the CachyOS package build of limine-entry-tool 1.40.0, and limine-snapper-sync 1.32.1. The upstream Limine bootloader is BSD-2-Clause. This module distributes the commissioned synchronization helpers and service definitions. Install the bootloader and its maintenance utilities from their respective distribution packages. [Limine 12.9.6 configuration](https://github.com/limine-bootloader/limine/blob/v12.9.6/CONFIG.md) · [limine-entry-tool](https://gitlab.com/Zesko/limine-entry-tool) · [limine-snapper-sync](https://gitlab.com/Zesko/limine-snapper-sync)

The user renderer reads illogical-impulse settings, the wallpaper file, and Matugen's generated palette and source record. It pairs them before sending the rendered 1920×1080 QOI and six contrast-validated colors. Pillow supplies blur and darkening. FFmpeg decodes the local image or the first frame of a supported video. The existing SDDM helper supplies media validation and safe path handling. The startup service reconciles the actual ESP digests. Path events reconcile updates, keeping the last matched pair while files arrive. Socket acknowledgements are digest-checked and retried.

The root-owned, socket-activated publisher uses mode 0600 and checks peer UID. It verifies image size and structure, the requested palette, the managed wallpaper path, and the boot protection state. It takes the same lock inode as the CachyOS maintenance tools and updates only the six allowed global colors plus the managed asset. It stages replacements and rollback copies before renaming. A sudden power loss between renames is reconciled on the next user-manager run. systemd-tmpfiles creates the boot-time lock without replacing its inode. The publisher unit grants the ESP parent write access for atomic rename and masks the known kernel and EFI paths read-only. The installer derives its UID, mount point, and machine entry directory locally.

## Reproduce on a compatible host

Provision a bootable, native CachyOS Limine installation first. Use a root-owned writable FAT ESP and the CachyOS package's active EFI binary. The baseline expects Secure Boot to be inactive and Limine configuration enrollment to be off. Keep the existing state and payload verification flags. Check that your own boot and recovery entries work before adding this layer. First install the SDDM media helper and configure the illogical-impulse/Matugen outputs.

Set `esp` to the actual mount point and `account` to the intended user's login. Run the installer from an unprivileged shell. `plan` generates and checks the host substitutions locally and lists destinations. `preflight` uses read-only sudo operations and validates the platform.

```sh
python -B system/limine/install.py plan --user "$account" --esp "$esp"
python -B system/limine/install.py preflight --user "$account" --esp "$esp"
```

Run the offline menu helper against a permission-restricted copy of this host's generated menu. Review the visual header diff. Keep the boot entries, payload hashes, default selection, and fallback entries. The helper preserves existing palette values and seeds the six fields only where missing. It enables fullscreen wallpaper, fades the normal terminal tint through the outer 64 pixels, and retains automatic font scaling and the interface resolution. Scaling preserves the aspect ratio on 16:9 framebuffers. A different framebuffer aspect ratio can stretch the image.

```sh
umask 077
stage=$(mktemp -d)
sudo cat -- "$esp/limine.conf" > "$stage/limine.conf"
python -B system/limine/prepare-menu.py "$stage/limine.conf" > "$stage/proposed.conf"
diff -u "$stage/limine.conf" "$stage/proposed.conf"
```

Use the native tooling for changes to `/etc/default/limine`. In the local `KERNEL_CMDLINE[default]` setting, retain storage, root, hardware, and recovery arguments. Remove `quiet` and `splash` from the intended normal and LTS profiles, then add `loglevel=6 systemd.show_status=true plymouth.enable=0` once. Carry the same change to the intended current text entries through the native tools. Historical snapshots retain their captured arguments. Review the tool's output and detect whether it regenerated the menu before staging the visual header. [CachyOS kernel command configuration](https://wiki.cachyos.org/configuration/boot_manager_configuration/#kernel-command-configuration)

For an existing synchronization installation, pause the user watcher and root socket instances before replacement. Keep the existing lock inode. For a new installation, an administrator can install the reviewed tmpfiles rule first and run `sudo systemd-tmpfiles --create /etc/tmpfiles.d/ii-limine-boot-lock.conf`. While holding `/run/lock/boot-partition.lock`, verify the current menu still matches the staged input, save a permission-preserving root-only copy, and rename the proposed file into place from the same mounted filesystem. Update this host's menu only. Check both entries and their referenced hashes before activating the service.

```sh
python -B system/limine/install.py install --user "$account" --esp "$esp"
sudo systemd-tmpfiles --create /etc/tmpfiles.d/ii-limine-boot-lock.conf
sudo systemctl daemon-reload
sudo systemctl enable --now ii-limine-wallpaper.socket
systemctl --user daemon-reload
systemctl --user enable --now ii-limine-render.path ii-limine-render.service
```

Run the two user commands as the target user. The home directory, platform, active desktop session, monitor and account setup are prerequisites. Enable user lingering only if the account and home storage can safely start before login; the existing reference implementation uses it. The watcher paths assume the normal illogical-impulse XDG layout. A full fresh-install or alternate ESP layout activation remains untested.

## Restore and verify

The installer prints a root-only backup directory when files change. Its manifest records which paths previously existed. Stop the watcher and socket before restoring. Copy listed present files from that directory to their original paths with `cp -a` and remove any listed absent files only after confirming those paths still belong to this installer. Reload both systemd managers and re-enable the previous units where applicable. Keep the shared lock file in place.

To reverse the visual and verbosity edits, restore the previous header fields and the local persistent kernel arguments from the administrative backups. A full old menu can overwrite more recent kernel or snapshot entries, so compare the current entry body and restore only the affected values if the body changed. Use the same shared lock and stage any ESP file replacement on the ESP. The regular, LTS and recovery entries should remain available. If necessary, use the distro's trusted live USB to mount the actual target filesystem and ESP and restore the affected files from the local administrative backup. The mount locations, device identifiers and recovery data are host-local.

The reference machine verified the installed theme in QEMU/OVMF at 1920×1080 and 2560×1440. On a new host, run the palette tests with `PYTHONPATH=system/limine/files python -B -m unittest discover -s system/limine/tests`. Review the user's `ii-limine-render.service` log for a matched palette and wallpaper and inspect the menu through an isolated read-only ESP image or a separately planned manual reboot.
