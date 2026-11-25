# Linux desktop configuration

Phase 1 captures a working CachyOS desktop running Hyprland and end-4's illogical-impulse. The reference installation uses a password-authenticated SDDM Material You greeter, native GNOME Keyring PAM integration, a Keyring-aware Brave shortcut, and a coordinated Limine wallpaper and color publisher.

Start with the [baseline inventory](docs/BASELINE.md) and [installation limits](docs/INSTALLATION.md). Run `scripts/doctor` as your desktop user to check an existing installation. Review [backup and recovery](docs/BACKUP_AND_RESTORE.md) before using any system component.

- [Architecture](docs/ARCHITECTURE.md) and [roadmap](docs/ROADMAP.md)
- [Agreed project plan](docs/PROJECT_PLAN.md)
- [Security and publication policy](docs/SECURITY.md)
- [Upstream dependencies and attribution](docs/UPSTREAM.md)
- [Changelog](docs/CHANGELOG.md)
- [Reference package manifest](packages/arch/reference.tsv)
- [Maintenance audit](docs/MAINTENANCE.md) and [optional Steam Material adapter](shared/applications/steam-material/README.md)
- [Hyprland and ii profile](profiles/hyprland/illogical-impulse/README.md)
- [SDDM](system/sddm/README.md), [Keyring and Brave guard](system/keyring/README.md), and [Limine](system/limine/README.md)

Only the Phase 1 combination is supported. A fresh installation has not been qualified end to end.
