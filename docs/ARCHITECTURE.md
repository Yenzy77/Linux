# Architecture

The [agreed project plan](PROJECT_PLAN.md) defines the scope, candidate profiles, and roadmap. This page describes how the baseline implements those boundaries.

The only supported distribution and desktop/profile combination is CachyOS with Hyprland and end-4 illogical-impulse. The profile owns its Hyprland, Quickshell, Matugen and user application preferences. Package dependencies are recorded separately. Host settings are local inputs.

SDDM performs password authentication and opens the GNOME Keyring session through PAM before Hyprland starts. The illogical-impulse lock stays in charge of normal locking. The Super+W guard checks Secret Service readiness before Brave launches. SDDM and Limine consume the same Matugen output produced by ii. Each has a separate publication socket and permissions. The greeter reads published assets from its own directory. The Limine renderer works as the desktop user, and its privileged publisher validates assets and edits a fixed allowlist while holding the same boot lock as the kernel and snapshot tools.

## Future boundaries

| Layer | Expected responsibility |
| --- | --- |
| Distribution adapter | Package names and sources, prerequisites, supported boot integration, and distro-specific validation. CachyOS and Arch come first. |
| Desktop adapter | Install prerequisites and own the compositor or desktop session startup and shutdown contract. |
| Dotfiles profile | Version-pinned profile configuration, scoped migrations, session readiness, and adapter compatibility. |
| Shared configuration | Deliberately shared applications, safe defaults, package metadata, and host-local settings. |
| Appearance | A profile can publish wallpaper provenance and semantic colors. Consumers opt in through a stable data contract. |
| Privileged system integrations | Authenticated display manager, fixed publication interfaces, bootloader assets, and coordinated platform updates. |

Log out, select a desktop and profile through SDDM and sign in again. A future session wrapper can select the profile and enter that desktop's lifecycle. SDDM PAM, the Login collection, and fail-closed browser protection remain centralized. Keep the login greeter independent of profile-owned code.

`XDG_CONFIG_HOME` covers only part of profile state. Programs also use XDG data, state, cache and runtime paths, fixed paths under the home directory, D-Bus names, systemd user units, portal backends, compositor sockets, and persistent environment imported into the user manager. Define what is shared explicitly. Isolate writable profile state, stop session resources on logout, and prevent competing services from claiming the same sockets or API names. Until verified, profile switching should assume one graphical session at a time.

Each layer needs preflight, backup, restore and a health check. User backups and boot/system backups have independent recovery paths. Boot changes need an explicit local menu review and the shared lock. Test profile activation and rollback in disposable environments before advertising support.

## Planned extensions

App adapters would consume the active profile's validated wallpaper or semantic palette and update only their own declared outputs. Each optional adapter would advertise compatibility, permission boundary, opt-in status, reconciliation and rollback. The Phase 1.1 Steam module is a manual Matugen adapter. It does not provide a system-wide adapter framework. A future optional Plymouth adapter would handle assets separately from boot verbosity and require explicit approval for any initramfs regeneration.

Upstream repositories and distribution ISOs are prospective configuration sources. Intake should pin provenance and integrity, extract into an isolated read-only or disposable workspace, inspect package hooks and licenses, and adapt individual reviewed files. Never run embedded installers or import identities, secrets, binaries or machine state. An optional ISO Builder would be a later consumer of validated manifests with reproducible staging and VM installation/recovery checks.

The future GUI would expose manifest installation and updates, activation and compatibility checks, backups and restore, upstream pin management, Git changes and system diagnostics. It should use the same reviewed operations as the CLI and keep privileged actions explicit. Systems with custom desktop packages also need pre-update dependency and recovery checks and post-update ABI and runtime validation. See the [maintenance audit](MAINTENANCE.md).
