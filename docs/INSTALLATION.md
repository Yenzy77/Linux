# Installation

This baseline documents and captures the CachyOS + Hyprland + illogical-impulse reference. Test deployment in a disposable CachyOS machine or VM first. Run as a regular desktop user unless a component explicitly calls for administrator rights.

1. Review [reference packages](../packages/arch/reference.tsv) and [upstream pins](UPSTREAM.md). Install the supported base profile according to its upstream guide. Resolve fonts and the user's licensed wallpaper separately.
2. Review the [profile README](../profiles/hyprland/illogical-impulse/README.md) and its allowlist. Use its preflight and dry run. Keep local display, hardware and application settings separate.

   Run `scripts/install --upstream /path/to/dots-hyprland` for the dry run. Only the explicit `--apply` option modifies target user files.
3. Review [SDDM](../system/sddm/README.md), [Keyring](../system/keyring/README.md), and the current display-manager configuration. Inspect effective PAM includes and arrange access to a recovery TTY before a later login test. The reference fallback is Maya.
4. Review [Limine](../system/limine/README.md) against the host's existing boot setup. Generate kernel and snapshot entries using that host's native tools. Back up and verify the live menu, lock, payload hashes and EFI fallback before any explicit visual edit. Retain host parameters and enrollment settings.
5. Use [backup and restore](BACKUP_AND_RESTORE.md) and run `scripts/doctor` as the desktop user. Test password login, regular locking, live appearance changes and a manual reboot only within an approved test environment.

The reference uses explicit installers and small module manifests. Chezmoi could manage user templates and supports dry-run and diff, but adds a second source-of-truth format before a second profile exists. This phase uses reviewed overlays with explicit backup, diff or dry-run behavior, and keeps system changes in their own components. Reconsider chezmoi if state drift and multi-host user templates justify it.

A fresh deployment, package bootstrap, arbitrary firmware and enrolled Secure Boot, and cross-distribution installation are unqualified. Host-specific settings, package availability and any upstream revision ambiguity require review before deployment. The current desktop was inspected without applying its installers.
