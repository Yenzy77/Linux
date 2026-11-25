# Reference packages

`reference.tsv` records selected package versions on the working CachyOS host. It is a compatibility inventory. It does not lock a package transaction or reproduce the complete installed OS. Resolve packages from trusted CachyOS and Arch sources and follow the pinned profile's upstream setup instructions for its meta-packages. Brave is optional for the system as a whole and required to use the Brave shortcut. The manifest does not install or upgrade packages.

The `reference_version` column records the original capture. `observed_at_publication` records the versions found when publication resumed. Several packages had changed. The later inventory and read-only health checks do not qualify those versions for fresh deployments.

The `phase_1_1_observed` column records the read-only maintenance audit. A dash in an older column means that package was outside the earlier inventory. Packages added in Phase 1.1 are optional unless a component declares a dependency. The Arch Rust package supplies both `rustc` and `cargo`. Versions indicate package state, including locally built packages that may keep the same version after a rebuild.
