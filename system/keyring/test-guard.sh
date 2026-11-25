#!/usr/bin/bash
set -euo pipefail
guard="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/browser-with-keyring"
tmp=$(mktemp -d)
trap 'rm -rf -- "$tmp"' EXIT
export GUARD_RECORD="$tmp/record"
cat > "$tmp/busctl" <<'STUB'
#!/usr/bin/bash
case "$GUARD_FIXTURE:$*" in
    missing:*) exit 1 ;;
    noalias:*ReadAlias*) echo 'o "/"' ;;
    *ReadAlias*) echo 'o "/org/freedesktop/secrets/collection/login"' ;;
    ready:*get-property*) echo 'b false' ;;
    locked:*get-property*) echo 'b true' ;;
    *) exit 1 ;;
esac
STUB
for program in notify-send brave google-chrome-stable firefox; do
    cat > "$tmp/$program" <<'STUB'
#!/usr/bin/bash
printf '%s\n' "${0##*/}" >>"$GUARD_RECORD"
STUB
done
chmod +x "$tmp/"*
mv "$tmp/google-chrome-stable" "$tmp/chrome.disabled"
for case in locked missing noalias; do
    : >"$GUARD_RECORD"
    if PATH="$tmp" GUARD_FIXTURE="$case" "$guard"; then
        exit 1
    fi
    [[ $(<"$GUARD_RECORD") == notify-send ]]
done
: >"$GUARD_RECORD"
PATH="$tmp" GUARD_FIXTURE=ready "$guard"
[[ $(<"$GUARD_RECORD") == brave ]]
mv "$tmp/chrome.disabled" "$tmp/google-chrome-stable"
: >"$GUARD_RECORD"
PATH="$tmp" GUARD_FIXTURE=missing "$guard"
[[ $(<"$GUARD_RECORD") == google-chrome-stable ]]
mv "$tmp/google-chrome-stable" "$tmp/chrome.disabled"
mv "$tmp/brave" "$tmp/brave.disabled"
: >"$GUARD_RECORD"
PATH="$tmp" GUARD_FIXTURE=missing "$guard"
[[ $(<"$GUARD_RECORD") == firefox ]]
printf 'Guard fixture passed: locked, missing, invalid alias, unlocked, first-choice Chrome, and Firefox fallback.\n'
