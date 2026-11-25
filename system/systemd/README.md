# systemd ownership boundaries

System and user units are stored alongside the SDDM and Limine components that use them. The profile's user manager owns the watcher and renderer. Socket-activated system services own publication. Unit interdependencies and file ownership must be reviewed with the component's installation notes.

The Limine socket depends on boot-time initialization of Limine's existing shared lock. Authentication remains in SDDM PAM. The normal desktop lock is managed by illogical-impulse.
