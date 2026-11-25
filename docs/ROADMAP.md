# Roadmap

The [agreed project plan](PROJECT_PLAN.md) is the source for candidate profiles, sequencing, and acceptance gates. This page is the implementation checklist.

| Phase | Acceptance criteria |
| --- | --- |
| 1. CachyOS + Hyprland + illogical-impulse baseline | Sanitized capture is reviewed and versioned. Current login, lock, browser guard and appearance sync pass non-invasive checks. Recovery is documented. |
| 2. Desktop Profile Manager foundation | Define the profile manifest, state ownership, lifecycle contracts, dry run, inventory and rollback. Prove one isolated test profile. |
| 3. Repair and complete KDE Plasma | Diagnose the existing failure, install the missing supported components, and verify native Breeze login/logout and rollback. |
| 4. KDE Plasma Material You | Accept shared wallpaper and semantic colors, confirm reversible Plasma integration, and keep Breeze selectable. |
| 5. Isolated Niri + iNiR | Verify separate session state, portal and service lifecycle, login/logout and coexistence with Hyprland. |
| 6. Additional Hyprland and Niri profiles | Qualify one profile at a time against adapter, isolation and restore checks. |
| 7. Profile selection through SDDM | Select installed profiles on logout/login while preserving PAM Keyring unlock and session cleanup. |
| 8. Shared wallpaper and palette | Test opted-in profiles with wallpaper changes, delayed color outputs and last-good recovery. |
| 9. Distribution adapters and clean installations | First qualify CachyOS and Arch with reproducible install, rollback and reboot tests. Evaluate EndeavourOS, Fedora and openSUSE Tumbleweed later. |
| 10. Optional graphical manager | Provide inspectable dry runs, clear authorization boundaries and equivalent CLI recovery. |

The reference host has `plasma-workspace` and KWin installed. `plasma-desktop` is missing. Prior observation showed `plasma-plasmashell.service` repeatedly exiting with status 1. The exact cause remains open for Phase 3. Phase 1 makes no Plasma changes.
