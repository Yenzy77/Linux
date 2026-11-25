# Login keyring and Brave guard

The reference CachyOS SDDM package includes `pam_gnome_keyring.so` in the `auth` and `session` sections of `/etc/pam.d/sddm`; the session hook uses `auto_start`. The system installer checks this native chain. The empty `User=` and `Session=` entries in the SDDM drop-in disable passwordless login. Password login supplies the same authentication token to PAM and the existing GNOME Login keyring. A previously changed keyring password may still require separate recovery.

The reference failure occurred because SDDM autologin supplied no authentication token to unlock the keyring. Starting a daemon alone could register Secret Service while leaving the collection locked. A redundant session startup daemon and the ii lock screen's keyring restart workaround were disabled. Normal lock and idle handling remain in the profile.

The Super+W binding invokes `/usr/local/lib/ii-sddm-sync/browser-with-keyring`. It preserves the existing browser search order and only gates Brave. The guard uses the Secret Service Login alias and the collection's public locked flag. It fails closed if the alias, service, or unlocked response is missing. It never queries any secret item or changes Brave's password backend. Launching Brave through other entry points bypasses this particular guard.

To validate a password login without starting any browser, run these in the user session.

```bash
busctl --user --auto-start=no get-property org.freedesktop.secrets \
  /org/freedesktop/secrets/collection/login org.freedesktop.Secret.Collection Locked
/usr/local/lib/ii-sddm-sync/browser-with-keyring --check-only
```

An unlocked Login collection returns `b false`. The guard reports the browser it would launch and, for Brave, whether the keyring would allow it. No browser databases, keyrings, passwords or PAM authentication logs belong in this repository.
