#!/usr/bin/bash
set -euo pipefail
umask 077
base=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
theme=/usr/share/sddm/themes/ii-sddm-theme
helpers=/usr/local/lib/ii-sddm-sync
mode=${1:---plan}
uid=$(id -u)
publisher=$(id -un)
pinned=$(<"$base/upstream.commit")
packages=(sddm qt6-declarative qt6-5compat qt6-svg qt6-virtualkeyboard qt6-multimedia-ffmpeg ffmpeg libnotify gnome-keyring python patch git)
targets=(
    /etc/sddm.conf.d/90-ii-sddm-theme.conf
    /etc/sddm.conf.d/zz-autologin.conf
    /etc/systemd/system/ii-sddm-sync.socket
    /etc/systemd/system/ii-sddm-sync@.service
    /etc/systemd/user/ii-sddm-publish.path
    /etc/systemd/user/ii-sddm-publish.service
    "$helpers/sync.py"
    "$helpers/browser-with-keyring"
    "$theme"
)
case "$mode" in
    --plan|--check|--build|--apply) ;;
    *) printf 'Usage: %s [--plan|--check|--build UPSTREAM NEW_OUTPUT|--apply UPSTREAM]\n' "$0" >&2; exit 2 ;;
esac
if [[ $mode == --plan ]]; then
    printf 'Use pinned upstream theme %s and install these system targets:\n' "$pinned"
    printf '  %s\n' "${targets[@]}"
    printf 'The existing SDDM PAM stack is checked. Reload only systemd unit definitions and start the local socket and publisher.\n'
    exit
fi
die() { printf '%s\n' "$*" >&2; exit 1; }
check_host() {
    [[ $uid != 0 && $publisher =~ ^[a-z_][a-z0-9_-]*$ ]] || die 'Run this as the intended desktop publisher.'
    [[ -r /etc/os-release ]] && grep -Eq '^ID="?cachyos"?$' /etc/os-release || die 'CachyOS is required.'
    pacman -Q "${packages[@]}" >/dev/null
    getent passwd sddm >/dev/null
    getent group sddm >/dev/null
    grep -Eq '^[-]?auth[[:space:]]+optional[[:space:]]+pam_gnome_keyring[.]so([[:space:]]|$)' /etc/pam.d/sddm
    grep -Eq '^[-]?session[[:space:]]+optional[[:space:]]+pam_gnome_keyring[.]so[[:space:]]+auto_start([[:space:]]|$)' /etc/pam.d/sddm
    [[ -r /usr/lib/security/pam_gnome_keyring.so ]] || die 'GNOME Keyring PAM module missing.'
    [[ -d /usr/share/sddm/themes/maya ]] || die 'Install the packaged Maya fallback first.'
    printf 'Required packages, SDDM account, PAM hooks and Maya fallback found.\n'
}
build_theme() {
    local checkout=$1 out=$2 source
    [[ $(git -C "$checkout" rev-parse --verify 'HEAD^{commit}') == "$pinned" ]] || die 'Upstream checkout must be at the documented commit.'
    source=$(mktemp -d)
    if ! (
        git -C "$checkout" archive "$pinned" | tar -xf - -C "$source" || exit 1
        if [[ -n $(find "$source" ! -type d ! -type f -print -quit) ]]; then
            exit 1
        fi
        python -IB "$base/build_theme.py" "$source" "$out" &&
            patch -d "$out" -p1 --batch --forward <"$base/patches/clock.patch" &&
            install -m 0644 "$base/patches/LICENSE" "$out/LICENSE"
    ); then
        rm -rf -- "$source"
        die 'Theme assembly failed.'
    fi
    rm -rf -- "$source"
}
if [[ $mode == --build ]]; then
    [[ $# == 3 ]] || die 'Supply a pinned checkout and a new output directory.'
    [[ ! -e $3 && ! -L $3 ]] || die 'Theme output already exists.'
    build_theme "$2" "$3"
    exit
fi
check_host
[[ $mode == --apply ]] || exit 0
[[ $# == 2 ]] || die 'Supply the pinned upstream checkout.'
# /etc/sddm.conf has highest priority. Require explicit administrator review
# for every other drop-in before activating login changes on a new host.
[[ ! -s /etc/sddm.conf ]] || ! grep -Eq '^[[:space:]]*[^#;[:space:]]' /etc/sddm.conf ||
    die 'Review and clear conflicting overrides in /etc/sddm.conf first.'
shopt -s nullglob
for conf in /etc/sddm.conf.d/*.conf; do
    case "$conf" in
        /etc/sddm.conf.d/90-ii-sddm-theme.conf|/etc/sddm.conf.d/zz-autologin.conf) ;;
        *) die "Review administrator drop-in before installation: $conf" ;;
    esac
done
stage=$(mktemp -d)
trap 'rm -rf -- "$stage"' EXIT
build_theme "$2" "$stage/theme"
cp "$base/units/"* "$stage/"
sed -i "s/@PUBLISHER_USER@/$publisher/" "$stage/ii-sddm-sync.socket"
sed -i "s/@PUBLISHER_UID@/$uid/" "$stage/ii-sddm-sync@.service"
systemctl --user show-environment >/dev/null
sudo -v
for target in "${targets[@]}"; do
    if sudo -n test -L "$target"; then die "Refusing symbolic-link destination: $target"; fi
done
# Preserve the production directory on an equivalent rerun. An existing theme
# with any changed files requires review and manual archiving before replacing.
theme_exists=0
if sudo -n test -e "$theme"; then
    [[ -f $theme/UPSTREAM-COMMIT && $(<"$theme/UPSTREAM-COMMIT") == "$pinned" ]] ||
        die 'Archive the existing theme before installing.'
    diff -qr --exclude=ii-sddm.conf.user "$stage/theme" "$theme" ||
        die 'Archive the locally modified theme before installing.'
    [[ $(readlink -- "$theme/Themes/ii-sddm.conf.user") == /var/lib/ii-sddm-sync/theme.conf.user ]] ||
        die 'Existing publisher configuration link needs review.'
    theme_exists=1
fi
backup=$(sudo -n mktemp -d /root/ii-sddm-baseline.XXXXXXXX)
for target in "${targets[@]}"; do
    if sudo -n test -e "$target"; then
        sudo -n mkdir -p -- "$backup${target%/*}"
        sudo -n cp -a -- "$target" "$backup$target"
    fi
done
printf 'Preserved original files in %s\n' "$backup"
put() {
    local source=$1 destination=$2 mode=$3 temporary directory ownership permissions
    directory=${destination%/*}
    if ! sudo -n test -e "$directory"; then
        sudo -n install -d -m 0755 -- "$directory"
    fi
    if sudo -n test -L "$directory"; then die "Refusing directory symlink: $directory"; fi
    read -r ownership permissions < <(sudo -n stat -c '%u %a' -- "$directory")
    [[ $ownership == 0 ]] && (( (8#$permissions & 8#022) == 0 )) ||
        die "Destination directory must be root-owned and protected: $directory"
    temporary=$(sudo -n mktemp -- "$directory/.ii-sddm.XXXXXXXX")
    if ! sudo -n install -m "$mode" -- "$source" "$temporary" ||
       ! sudo -n mv -T -- "$temporary" "$destination"; then
        sudo -n rm -f -- "$temporary"
        die "Unable to install $destination"
    fi
}
if (( ! theme_exists )); then
    while IFS= read -r -d '' relative; do
        put "$stage/theme/$relative" "$theme/$relative" 0644
    done < <(find "$stage/theme" -type f -printf '%P\0')
    sudo -n ln -s -- /var/lib/ii-sddm-sync/theme.conf.user "$theme/Themes/ii-sddm.conf.user"
fi
put "$base/sync.py" "$helpers/sync.py" 0644
put "$base/../keyring/browser-with-keyring" "$helpers/browser-with-keyring" 0755
for unit in ii-sddm-sync.socket ii-sddm-sync@.service; do
    put "$stage/$unit" "/etc/systemd/system/$unit" 0644
done
for unit in ii-sddm-publish.path ii-sddm-publish.service; do
    put "$stage/$unit" "/etc/systemd/user/$unit" 0644
done
sudo -n systemd-analyze verify /etc/systemd/system/ii-sddm-sync.socket /etc/systemd/system/ii-sddm-sync@.service
systemd-analyze --user verify /etc/systemd/user/ii-sddm-publish.{path,service}
sudo -n systemctl daemon-reload
sudo -n systemctl enable --now ii-sddm-sync.socket
systemctl --user daemon-reload
systemctl --user start ii-sddm-publish.service
sudo -n runuser -u sddm -- test -r "$theme/Themes/ii-sddm.conf.user"
systemctl --user enable --now ii-sddm-publish.path
put "$base/config/zz-autologin.conf" /etc/sddm.conf.d/zz-autologin.conf 0644
put "$base/config/90-ii-sddm-theme.conf" /etc/sddm.conf.d/90-ii-sddm-theme.conf 0644
printf 'Theme and socket installed. Take effect at the next planned SDDM start.\n'
