# Backup, restore and recovery

Keep backups outside the checkout. A separate Btrfs home subvolume needs its own backup; a root Snapper snapshot does not protect it. ESP files also need a separate copy. Keep backups local and access-restricted.

Run `scripts/backup` as the desktop user to snapshot only profile-managed files. Use `scripts/restore /path/to/private/backup` to restore one. Restore refuses to overwrite files changed since that snapshot unless you explicitly pass `--replace-changed` after reviewing the affected paths. Both commands accept `--config-root` for fixture testing. The apply command takes its own rollback backup automatically. System component backups are separate.

- User overlays should record the prior files and which destinations were absent. Restore the specific paths while respecting later local changes. Keep generated theme caches separate from configuration.
- Before SDDM changes, back up the effective configuration, PAM files, theme and custom units with permissions preserved. Keep a known working greeter available. If the theme fails at next login, switch to a recovery TTY and restore the previous effective theme setting. A display-manager restart terminates graphical sessions. Schedule it only after recovery review.
- Never reset the GNOME Login collection for ordinary PAM recovery. Inspect whether a password-authenticated SDDM session opens it, and use the guard's check-only mode before opening Brave.
- Before Limine changes, back up the host menu and assets, confirm the EFI fallback path, and record the boot entry tree and payload hashes. Acquire the existing boot lock before an atomic replacement. If later kernel or snapshot updates changed the menu, restore the visual settings into the latest menu and keep the newer entries. Do not replace it with an older full menu.
- If Limine fails, use a verified firmware fallback or a compatible live USB. Identify the correct volumes before mounting them and follow the appropriate CachyOS recovery procedure. A snapshot rollback is a separate recovery decision.

System component documentation contains the local installation and recovery boundaries. Re-check service ownership and socket permissions after any restore.
