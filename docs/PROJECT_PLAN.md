# Linux desktop configuration: project plan

Status: agreed design and roadmap, 2026-11-26. This document records planning decisions, not a claim that the configuration has already been exported, installed on a fresh system, or tested on every distribution.

## 1. Purpose and scope

Build a reproducible, modular Linux desktop configuration repository that preserves the current working CachyOS workstation, supports multiple desktop environments and multiple dotfiles profiles per desktop, and can eventually be used on another machine or distribution without reinstalling Linux just to change a desktop or visual style.

The first milestone is deliberately limited to the existing CachyOS + Hyprland + illogical-impulse (ii, by end-4) desktop. Capture the real personalized configuration, not a replacement with upstream defaults. KDE Plasma, Niri, additional profiles, and additional distributions are future phases.

The repository is public. It is a source of reviewed configuration, templates, scripts, documentation and dependency manifests, not a backup of personal data or secrets.

## 2. Target user experience

One Linux installation, one shared account and application/data set where compatible, and multiple selectable graphical sessions. A user can log out, select a desktop and its configuration profile in SDDM, then log in again without a reboot or OS reinstall. Preserve a known-good Hyprland session as a recovery option. Live changes to wallpaper, colors and individual settings are welcome; switching complete desktop stacks should normally require logout to avoid conflicting processes.

Illustrative future SDDM choices (not installed or supported yet):

- Hyprland (illogical-impulse)
- Hyprland (HyDE)
- Hyprland (ML4W)
- Hyprland (Caelestia)
- Hyprland (DankMaterialShell)
- Plasma (Breeze)
- Plasma (Material You)
- Plasma (end-4-inspired), optional
- Niri (iNiR)
- Niri (DankMaterialShell)
- Niri (Noctalia)

Only expose sessions that have been installed, validated and enabled. A single desktop may have multiple profiles, and a profile may be installed without activating it. The list is a candidate set, not a commitment to maintain every upstream project.

## 3. Architecture

```text
Linux distribution / hardware adapter
  |-- Shared package and application configuration
  |-- Optional system integrations (Limine, SDDM, PAM, systemd)
  |-- Desktop session / profile manager
      |-- Hyprland: ii, HyDE, ML4W, Caelestia, DMS
      |-- KDE Plasma: Breeze, Material You, optional ii-inspired
      |-- Niri: iNiR, DMS, Noctalia
  |-- Active profile appearance adapter
      |-- Wallpaper + palette publication
      |-- SDDM and Limine consumers (when installed and compatible)
```

Separate distribution-specific package installation, shared user settings, profile-specific desktop configuration, and root-owned system integration. Use a modular manifest for each profile: upstream reference and version, supported compositor/shell version, dependencies, managed paths, startup/shutdown services, appearance adapter, conflicts and rollback procedure.

Evaluate chezmoi for shared user files and portable templates; it is not itself a complete desktop profile manager. Prefer simple explicit scripts and manifests for profile activation and privileged provisioning. Do not require a framework or package manager that adds complexity without a clear benefit. The concrete implementation choice should be documented in the baseline.

### Profile isolation and lifecycle

- Keep profiles independently versioned and preserve user customizations when switching or updating.
- Use compositor-supported config selection, controlled symlinks or a managed activation mechanism as appropriate. Generate SDDM session entries only for validated profiles; do not overwrite the working fallback entry.
- Audit literal ~/.config paths, XDG_CONFIG_HOME, XDG_DATA_HOME, XDG_STATE_HOME, caches, environment imports, desktop portals, user units, DBus names, and autostart scripts. Changing XDG_CONFIG_HOME alone is not sufficient because upstream tools can hardcode paths and systemd user services are shared.
- Stop profile-owned services and clear stale profile-specific environment on logout; avoid concurrent wallpaper managers, notification daemons, lock screens, desktop shells or color generators.
- Preserve application settings/data that are intentionally shared; isolate settings that conflict. Never copy or redirect browser profiles into an unvalidated configuration.
- Do not run upstream installers blindly over an existing workstation. Inspect their write paths, package changes, services, migration scripts and prerequisites first. Use isolated test accounts, temporary homes or VMs for experiments.
- Activation must be reversible. A failed profile must not prevent login to the known-good desktop. Record active profile and backups locally, not as machine-specific state in Git.

### Appearance integration

The current reference implementation uses ii wallpaper and Matugen output to synchronize desktop, lock screen, SDDM and Limine. The future abstraction should allow each active profile to supply a normalized wallpaper and palette through an adapter without running several color managers at once.

Preserve the last successfully matched wallpaper/palette when updates arrive separately or publication fails. Validate input, debounce changes, reconcile at login, retry failed publication, and skip redundant writes. Keep profile-specific visual identity where desired; shared synchronization must be configurable rather than forcing every profile into one theme.

## 4. Phase 1: capture the existing reference workstation

The current working configuration was repaired and tested locally in prior sessions. Its sanitized export is being prepared separately. Record actual file paths, versions, provenance, implementation reports and validation evidence in the baseline; do not infer them from this plan.

| Area | Required capture |
| --- | --- |
| Hyprland | Active configuration format, keybinds, window rules, animations, startup and personal overrides |
| illogical-impulse | Quickshell, settings, widgets, lock screen, wallpaper and Matugen integration; custom monitoring changes if present |
| Shared user settings | GTK/Qt appearance, Kitty, Fish, prompt, fonts and reviewed application settings |
| SDDM | ii + Matugen theme based on 3d3f, clock fixes, secure wallpaper/palette publisher, fallback theme, native login with autologin disabled |
| Keyring | Native SDDM PAM unlock and non-invasive checks, no credential databases |
| Brave | Launch guard for locked/unavailable GNOME Keyring and corresponding Hyprland shortcut; no browser data |
| Limine | Dynamic wallpaper, pre-rendered blur/darkening, Matugen menu/help/selection colors, native font/automatic scaling, fullscreen wallpaper, three-second countdown, verbose boot |
| System services | Actual user/system units, watchers, sockets, publisher scripts, startup reconciliation/retry, shared boot lock initialization and permission requirements |
| Packages and hardware | Reviewed package manifests, upstream pins where available, optional hardware-specific templates and local overrides |
| Recovery | Backup, rollback, TTY recovery, SDDM fallback and boot recovery instructions |

### Reference implementation invariants

- Keep native SDDM authentication; do not reintroduce autologin followed by a forced startup lock. Preserve manual, idle and sleep locking. The previous incident showed that login without a password left GNOME Keyring locked and Brave sessions became unavailable.
- Keep the Brave encryption backend compatible with existing data. Never reset Keyring or switch storage backend just to make another desktop work. Guard checks must not reveal secrets or open browser data.
- Preserve Limine normal/LTS kernel entries, snapshots, EFI fallback, default boot behavior, payload integrity hashes and verbose parameters. The current reference validation included 22 snapshots and 15 payload hashes; these are historical measurements, not portable constants.
- Preserve wallpaper preprocessing and the native font. The custom 8x16 bitmap experiment was reverted for readability. Fullscreen configuration uses stretched wallpaper and a wider terminal margin gradient; physical edge-to-edge verification was still pending in the last report for that revision.
- Preserve the shared boot partition lock. A missing /run/lock/boot-partition.lock after reboot caused publication failures; boot-time initialization, startup reconciliation and retry were added. Maintain compatibility with installed Limine management tools.
- Retain secure publisher boundaries, fixed destinations, allowlisted color fields, strict validation, safe replacement and existing integrity protections. No unrestricted ESP writes, user-writable root scripts, broad passwordless sudo or disabled verification. FAT does not provide an atomic transaction spanning multiple files; document interruption recovery.
- Avoid copying machine-specific raw boot configuration. Discover boot layout and identifiers on the target, modify only supported settings, and coordinate with kernel and snapshot updates.
- Latest measured boot after verbose boot/countdown changes: 27.948 seconds versus 30.268 seconds previously. This is a historical single-machine measurement, not a performance guarantee.

Phase 1 is capture and reproducibility work, not permission to change the live desktop. Validate with read-only health checks and isolated test environments; do not run an installer on the current working machine merely to demonstrate it.

## 5. Desktop candidates and sequence

### KDE Plasma

Plasma should provide a distinct, traditional KDE/KWin experience alongside tiling desktops. Start with native Breeze, then evaluate KDE Material You Colors, Utterly Round and Klassy for a native Material-inspired profile. An end-4-inspired KDE port is optional and requires additional compatibility review.

Current observed issue: plasma-workspace, KWin, plasma-nm and plasma-browser-integration are installed; plasma-desktop is missing. The Plasma Wayland session starts but displays a black desktop with a cursor; CachyOS Hello appeared. plasma-plasmashell.service repeatedly exited with status 1 and hit the systemd start limit. No coredump was listed. Incomplete installation is a strong hypothesis, not a proven root cause. Investigate the actual error and package versions before completing Plasma. Do not repair it during baseline capture.

Acceptance: usable native desktop, panel, launcher, wallpaper, settings, logout/login and return to Hyprland, no regression in shared credentials or portals. Test Brave backend compatibility without risking existing sessions before normal browser use. Then add Material You as a separately reversible profile.

### Niri

Niri offers scrollable tiling rather than Hyprland's dynamic tiling. Evaluate iNiR first for visual continuity with ii, then DMS or Noctalia. Audit the iNiR installer's configuration migrations, particularly any impact on existing illogical-impulse settings, and runtime/compositor version requirements. Keep the original ii profile intact. Acceptance: working scrolling/workspaces, shell, shortcuts, lock screen, portals, logout and re-entry, with shared appearance adapter and safe credential handling.

### Additional Hyprland profiles

Evaluate HyDE, ML4W, Caelestia and DankMaterialShell one at a time. Do not install all candidates in one transaction. Each must have an independent manifest, tested lifecycle and a reversible activation procedure.

Candidate upstream references (review current versions and licenses before use):

- ii: https://github.com/end-4/dots-hyprland
- HyDE: https://github.com/HyDE-Project/HyDE
- ML4W: https://github.com/mylinuxforwork/dotfiles
- Caelestia: https://github.com/caelestia-dots/caelestia
- DMS: https://github.com/AvengeMedia/DankMaterialShell
- iNiR: https://github.com/snowarch/iNiR
- Noctalia: https://github.com/noctalia-dev/noctalia-shell
- KDE Material You Colors: https://github.com/luisbocanegra/kde-material-you-colors
- Utterly Round: https://github.com/HimDek/Utterly-Round-Plasma-Style
- Klassy: https://invent.kde.org/paulm/klassy/
- Optional KDE port: https://github.com/ladybug-me/end-4dots-kde
- Configuration management candidate: https://github.com/twpayne/chezmoi

These references are evaluation candidates, not pinned or approved dependencies. Record actual upstream versions, licenses and attribution in the implementation documentation.

## 6. Proposed repository structure

```text
profiles/
  hyprland/illogical-impulse/
  plasma/                  # future
  niri/                    # future
shared/
  matugen/
  terminal/
  themes/
  applications/
system/
  limine/
  sddm/
  keyring/
  systemd/
packages/
  arch/
  fedora/                  # future
  opensuse/                # future
scripts/
  install
  backup
  restore
  doctor
  switch                   # future
  update                   # future
docs/
  PROJECT_PLAN.md
  ARCHITECTURE.md
  ROADMAP.md
  BASELINE.md
  INSTALLATION.md
  BACKUP_AND_RESTORE.md
  SECURITY.md
  UPSTREAM.md
  CHANGELOG.md
README.md
AGENTS.md
.gitignore
```

This is a design, not a requirement to create empty placeholders. Adjust layout to the actual configuration management approach. The detailed baseline docs should link back to this plan and distinguish implemented, locally tested, planned and unverified features.

## 7. Portability and provisioning

Prioritize CachyOS first, then Arch Linux and optionally EndeavourOS. Evaluate Fedora and openSUSE Tumbleweed after the Arch-family implementation is stable. Ubuntu/Debian may require additional compatibility work; NixOS needs a separate integration approach. No distribution may be advertised as supported without an actual installation test.

Use distro detection, per-distro package names, explicit compatible versions, preflight checks, optional system integrations, and separate user/root operations. Do not assume every distro uses SDDM, Limine, Btrfs, Snapper or the same PAM layout. Keep host-local paths, device identifiers and monitor/GPU settings in local overrides or templates. A future installer should offer selection of desktops, profiles and optional components; never require installing everything.

Provide dry-run, idempotent behavior where practical, backups, restore, health checks and clear error messages. Validate clean installs in isolated VMs, with separate physical tests for hardware/firmware-specific behavior. Preserve existing working configurations by default.

## 8. Public repository security, licensing and Git policy

Allowlist and review every tracked file and generated artifact before committing; scan staged changes and complete proposed Git contents before pushing. Do not publish keyrings, KWallet stores, browser cookies/profiles/passwords/history, SSH/GPG private keys, API tokens, AI credentials, hosting credentials, private projects, secret environment files, raw backups/logs, private account identifiers, machine-specific boot identifiers, caches or unauthorized wallpaper assets. Use a separate encrypted backup for sensitive state. A private repository would not remove the need for this discipline.

Prefer pinned upstream sources and personal overrides over copying third-party assets or entire projects. Preserve required licenses, notices and attribution; do not invent a blanket license for third-party material. Record uncertainties and block publication of affected files until resolved.

Use English for documentation, comments and commit messages. For local implementation commits, use the owner's existing author name and verified GitHub noreply address scoped to this repository, without AI co-author trailers. Do not force-push, change repository visibility, or overwrite another agent's work. Review and reconcile remote changes before publication.

Privileged integration must be opt-in, narrowly scoped, auditable and recoverable. Never store or expose credentials to prove functionality.

## 9. Roadmap and acceptance gates

| Phase | Scope | Gate before proceeding |
| --- | --- | --- |
| 1 | Capture current CachyOS + Hyprland + ii baseline | Sanitized actual configuration, manifests, docs, security/license checks, backup/restore/doctor and Git publication; no live regressions. Clearly mark untested clean-install behavior. |
| 2 | Desktop Profile Manager foundation | Manifest, isolation, activation/rollback and known-good fallback; test using a harmless isolated profile before touching live configurations. |
| 3 | Repair/complete native Plasma | Diagnose failure, verify package compatibility, validate normal login/logout and return to Hyprland. |
| 4 | KDE Material You customization | Separate reversible profile; native KDE workflow, appearance, no shared configuration/credential regression. |
| 5 | Isolated Niri + iNiR | Working Niri session; no overwrite of ii; independent config and services. |
| 6 | Additional profiles | Add one at a time; audit upstream installer, test coexistence and rollback. |
| 7 | Multiple profiles in SDDM | Explicit named sessions; correct activation, teardown and safe fallback. |
| 8 | Cross-profile appearance integration | Active profile publishes matched wallpaper/palette; preserve secure Limine/SDDM behavior, validate switching and failed updates. |
| 9 | Multi-distribution installer | Clean VM installs, dry-run, restore, compatibility matrix; advertise only tested combinations. |
| 10 | Optional GUI profile manager | Only after stable CLI/manifests; select, install, update, backup, restore and diagnose profiles without uncontrolled privileged actions. |

The ordering is intentional: protect the current working desktop first, then experiment. Phase 2 and later are not authorized by Phase 1.

## 10. Validation and operational guardrails

Before publication, review inventory, syntax, systemd units, dependencies, upstream/license records, documentation links, secret scans, staged changes, and recovery instructions. Verify current SDDM/Limine appearance watchers, Keyring unlocked status and Brave guard in check-only mode. Never access or test actual browser profile data for this purpose.

During baseline capture do not reboot, logout, restart SDDM, terminate Hyprland, install Plasma/Niri or alternative dotfiles, upgrade the system, alter PAM/boot behavior or overwrite the working desktop. Any later system change requires explicit phase scope, backup and rollback. Test boot changes in isolated QEMU/OVMF where appropriate, never attach the live boot disk writable, and leave physical reboot to the user.

## 11. Coordination and current status

At the time this plan is published, the local baseline capture is being handled separately by Codex Desktop and was interrupted by a usage limit. The remote repository had no initial commit when checked. This document is planning-only; the local implementation must retain its work, fetch the remote documentation commit, reconcile history safely before pushing, and link this plan in README. Do not force-push over the planning commit or duplicate the plan unnecessarily. Actual baseline completion, local file inventory, licensing evidence, fresh-install reproducibility and physical verification must be reported separately.

## 12. Phase 1.1 maintenance and planning addendum

Phase 1.1 refreshes package observations while preserving the historical inventory. It may capture optional application adapters that already exist on the reference workstation. Validate reported maintenance against installed packages and configuration, record unresolved runtime checks, and keep this work separate from Phase 2.

Add [Ryoku](https://github.com/Ryoku-dev/ryoku) and [Omarchy](https://github.com/basecamp/omarchy) to the candidate evaluation list. Treat upstream repositories and ISO images as sources for selective adaptation. Verify provenance and licenses, inspect artifacts in isolated staging, and avoid executing upstream installers or reusing machine identities. Any optional ISO Builder should consume validated manifests and produce disposable test images only after distribution adapters and recovery tests are established.

System-wide dynamic theming is a planned opt-in adapter model. Each application integration will declare its inputs, outputs, compatibility and rollback. Plymouth customization and dynamic theming are optional and require separate review of boot verbosity, asset permissions and initramfs changes.

The optional GUI Desktop Profile Manager is planned to cover installation, updates, activation, backup, restore, compatibility checks, upstream source management, Git integration and diagnostics. It should use the CLI's validation and authorization boundaries.

For custom desktop packages, plan pre-update checks for versions, sources, dependency changes and recovery options. Follow updates with package consistency, ABI and runtime checks. Document rebuild and recovery procedures without relying on unreviewed library substitutions.

See the [maintenance audit](MAINTENANCE.md) for observed evidence and pending tests. Later features remain outside Phase 1.1.
