# Hyprland and illogical-impulse

This overlay is based on the working ii installation and the clean local [end-4 checkout at `d192a25faa11cf1d56c839c344c9ef8dd6c2c69d`](https://github.com/end-4/dots-hyprland/tree/d192a25faa11cf1d56c839c344c9ef8dd6c2c69d). The contextual patch carries modified end-4 material under the upstream GPLv3 terms. The included [upstream license text](COPYING) applies to that material. Upstream's per-file notices and [license exceptions](https://github.com/end-4/dots-hyprland/tree/d192a25faa11cf1d56c839c344c9ef8dd6c2c69d/licenses) still apply.

## Captured

- Hyprland's active entry point is `hyprland.lua`. Its upstream modules supply the base animations, window rules, startup tasks, workspace bindings and Matugen colors. The patch records the portable shadow tuning, Super release behavior, startup and keyring adjustments, application preferences and Super+W's browser guard.
- The ii JSON overlay records approved settings for fonts, wallpaper theming, parallax, clock, lock behavior, sidebar, workspace labels, app pins and resource widget polling. The production lock path uses Quickshell. Hypridle retains idle locking, DPMS and sleep hooks. The optional Hyprlock fallback contains the reference user's localized display text.
- Quickshell's patch adds the existing GPU utilization widget and popup. The physical device path has been replaced by a local `II_GPU_BUSY_PATH` setting. It also retains both WARP toggle changes that prevent unsolicited registration.
- Matugen templates/config, shell files, common Kitty bindings, and Starship prompt are supplied by the pinned source. The Kitty sizing adjustment is patched. Generic Fish startup comes from upstream. Private CLI path additions, Fish universal variables and generated terminal themes stay local.
- The toolkit overlay records the GTK cursor, theme and font and the Qt/KDE style, fonts, icons and Material You scheme name. GTK CSS, Qt color definitions and other generated Matugen output are generated locally. Fonts, icons and visual assets come from the matching packages or rights-cleared local additions.
- Wallpaper paths, exact display outputs, legacy startup-lock stubs, the generated video restore helper, AI configuration and service credentials stay local. To equip the profile for a GPU that exposes utilization, select a readable file under `/sys/class/drm/card*/device/gpu_busy_percent` and merge the setting from [the GPU example](gpu-env.lua.example) into the local `hypr/custom/env.lua`. [The graphics example](graphics-local.lua.example) shows optional reference rendering and monitor settings. Review these on the target host before use.

## Overlay workflow

Install the pinned upstream profile on a fresh compatible test system through its documented process. Then invoke the overlay without sudo. The default invocation lists pending files and stages the patch in scratch space for validation. The explicit `--apply` mode saves original bytes and modes in a private backup before writing. `--restore` restores one backup and checks that changed files still match the installed digests. `--config-root` selects a fixture directory for isolated tests. The live profile expects the standard `~/.config` layout because several pinned upstream components refer to it directly.

```sh
python profiles/hyprland/illogical-impulse/install.py --upstream /path/to/dots-hyprland
python profiles/hyprland/illogical-impulse/install.py --apply --upstream /path/to/dots-hyprland
python profiles/hyprland/illogical-impulse/install.py --restore /path/to/private/backup
```

Apply during a planned setup while the target session is inactive. Install the system-side browser guard before using Super+W. Choose a locally licensed wallpaper in ii Settings to generate the Matugen assets. The profile fixtures verify preview, application, idempotence, and byte-for-byte restore. The fresh graphical install and runtime on alternate hardware remain to be verified.

Chezmoi offers declarative user file state, templates and useful diffs. For this phase the portable changes are a small patch against a pinned profile plus two merges into files owned by live applications. A Python standard-library overlay keeps that scope explicit and leaves package and boot changes to the privileged workflow. Reconsider chezmoi if several independent profiles make cross-host templating worthwhile. [Chezmoi source state](https://www.chezmoi.io/reference/source-state-attributes/)
