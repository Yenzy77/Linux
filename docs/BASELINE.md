# Baseline inventory

Reference host captured on November 26, 2026. Package versions are in the [reference package manifest](../packages/arch/reference.tsv). The component directories contain implementation details and any capture gaps.

| Area | Working reference |
| --- | --- |
| Desktop | CachyOS, Hyprland Lua entry points, and the end-4 illogical-impulse Quickshell session. The profile contains the reviewed settings and local overrides. |
| Login and locking | SDDM password login with autologin off. SDDM PAM unlocks the existing GNOME Login collection. ii handles Super+L, idle and sleep locking. |
| SDDM appearance | Pinned ii + Matugen theme, analog clock fixes and socket-activated publication. Greeter access and fallback are documented in the SDDM component. |
| Browser | Super+W resolves the configured browser and the Brave launch path checks Secret Service and the unlocked Login collection. |
| Limine | Cropped, blurred, darkened QOI wallpaper, dynamic menu colors, stretched framebuffer fill with a 64-pixel margin fade, native font and automatic scaling. Includes a three-second countdown and informational boot messages. |
| Publication | User watchers and renderer, privileged fixed-path validation, shared Limine lock with boot-time provisioning, acknowledgement and startup reconciliation. |
| Boot integrity | Host-generated normal, LTS, snapshot and fallback entries remain host configuration. Both EFI loaders and all 15 tracked payload hash references passed the reference verification after the fullscreen fix. |

The original login issue occurred when autologin supplied no password to PAM. The Keyring was unavailable during startup and Brave session access was disrupted. Password login and native PAM fixed the initialization sequence. The guard provides a check at launch even if the Secret Service later becomes unavailable. The wallpaper lock fix addressed the missing volatile lock on a fresh boot. The renderer now reconciles the installed state at startup and after change events.

Earlier live validation included password login, Keyring unlock, guard check, and validated browser session continuity. Limine preview validation compared actual EFI and published assets under isolated OVMF. The capture does not contain repair journals, screenshots of personal wallpaper, credentials, or boot artifacts.

## Validation

- The pinned ii overlay passed dry run, fixture apply and idempotence. The backup and restore commands were tested against a temporary configuration root. Restore refused an edited file until explicitly authorized and returned its prior bytes. Patched Hyprland Lua passed syntax checks.
- The pinned SDDM theme built in a temporary directory and matched the deployed theme except for its private runtime configuration link. The SDDM preflight found the packaged PAM hooks and Maya fallback.
- Six isolated Brave guard cases, three SDDM publisher tests and three Limine palette tests passed. The system and user service templates were materialized and checked with systemd.
- Live read-only checks found SDDM, both appearance watchers and both publisher sockets active. The Login collection returned `b false`. The guard passed in check-only mode. No live installer was run and no browser profile was accessed.
- Full graphical deployment and reboot on a new CachyOS system, alternate hardware and ESP layouts, and other distributions remain unverified.

Phase 1.1 adds separate [maintenance observations](MAINTENANCE.md) and an [optional Steam Material adapter](../shared/applications/steam-material/README.md). The original baseline observations above remain historical.
