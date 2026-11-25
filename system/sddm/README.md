# SDDM and illogical-impulse Material You

The production theme uses [3d3f/ii-sddm-theme](https://github.com/3d3f/ii-sddm-theme/tree/1d4bcb66647f750bcc14d73de025eae8dd1e3db7) at the exact revision in [upstream.commit](upstream.commit). The builder applies typed theme settings, Matugen colors, the wallpaper blur setting, fonts, and per-view geometry handling. The clock patch paints the face directly under Qt Quick software rendering and corrects hand layering and shape layout. The project includes the theme's GPLv3 text and patch source. Theme artwork, wallpaper and font binaries are obtained from the pinned upstream checkout at build time. Google Sans Flex is available under OFL 1.1 from [Google Fonts](https://github.com/google/fonts/tree/main/ofl/googlesansflex), and the bundled Fluent System Icons font carries Microsoft's MIT license and NOTICE. The builder preserves the upstream asset notices. The pinned theme's Google Sans Flex notice includes placeholder attribution, so this repository carries no copy of that font. The system cursor comes from the optional illogical-impulse Bibata package. Appearance aliases for expressive and reading fonts use the fonts supplied by the desktop profile.

The desktop sender watches the installed ii JSON and Matugen output, transcodes the selected media locally, validates lengths, and sends allowlisted values over an AF_UNIX socket. The receiver runs as the unprivileged SDDM account under systemd sandboxing. The socket is mode 0600 and the receiver checks the connecting UID. The live state directory is mode 0750 and owned by SDDM. Publication uses two asset slots and replaces the config only after the new assets are staged. The greeter configuration link addresses that directory. The greeter receives no home directory access or sudo permission. The same helper supplies portable file readers used by the Limine renderer.

## Prepare and verify

Run as the intended desktop user. Package dependencies come from the CachyOS and Arch repositories. Provision the compatible ii profile and generate a Matugen palette with a local wallpaper before installing. The installer verifies the packaged SDDM Keyring PAM hooks and Maya recovery theme. Save an existing customized SDDM configuration before installation and review any administrator drop-ins that conflict.

```bash
system/sddm/install.sh --plan
system/sddm/install.sh --check
git clone https://github.com/3d3f/ii-sddm-theme.git /tmp/ii-sddm-upstream
git -C /tmp/ii-sddm-upstream checkout --detach "$(cat system/sddm/upstream.commit)"
system/sddm/install.sh --build /tmp/ii-sddm-upstream /tmp/ii-sddm-preview
```

The explicit install command is `system/sddm/install.sh --apply /tmp/ii-sddm-upstream`. It uses interactive sudo, backs up previous targets under a root-only `/root/ii-sddm-baseline.*` directory, assembles the audited pinned theme without running its installer, materializes the socket account and UID, publishes the initial palette, and selects the theme with password authentication. It leaves the running display manager and session active. If an existing ii theme differs, the installer stops so an administrator can review and archive it.

An ordinary desktop-user preview can show the static fallback palette because the production assets are private to SDDM. From a working TTY or session, verify the greeter can read its published settings with `sudo -u sddm test -r /var/lib/ii-sddm-sync/theme.conf.user`. Use separate nested/offscreen test rendering as the SDDM account for a production preview. Keep the current graphical session running.

## Recovery

If the greeter fails, open a TTY and sign in. Keep the password-authenticated drop-in. Disable the custom theme selection and select the packaged Maya theme for the next planned SDDM start.

```bash
sudo mv -n /etc/sddm.conf.d/90-ii-sddm-theme.conf /etc/sddm.conf.d/90-ii-sddm-theme.conf.disabled
printf '[Theme]\nCurrent=maya\n' | sudo tee /etc/sddm.conf.d/95-recovery-maya.conf >/dev/null
```

For a full rollback, stop the two SDDM publishing units under the user manager and disable the SDDM publisher socket. Allow active receiver instances to exit. Restore individual archived files to the same absolute paths using `sudo cp -a`. Archive newly created files under root when they did not exist in the backup. Do not move the shared helpers while Limine uses them. Review any saved autologin settings before restoring them. Reload systemd managers and schedule display manager changes for the next boot.

The reference machine's password login and secure asset publication have been physically verified. This repository's isolated build was compared with the deployed theme, but the installer has yet to be applied on a fresh CachyOS image.
