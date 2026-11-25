# Optional Steam Material palette

This adapter captures the reference transport from ii/Matugen to the Material theme for Steam. Steam and Millennium are optional and are provisioned separately. The observed versions are in the [package manifest](../../../packages/arch/reference.tsv).

The installed Material skin reports 1.5.21. Its own Matugen source-color option uses the theme's JavaScript loader to request `css/main/colors/matugen.css`. The local Matugen template matched the theme's template byte for byte. This copy preserves the CSS template and omits upstream's setup comment. The accompanying [MIT notice](LICENSE) applies. This module distributes no Steam, Millennium or theme binaries, plugins, artwork, account settings, client state or generated CSS. [Material upstream](https://github.com/kuska1/Material-Theme) · [Millennium 3.7.0 Beta 2 release](https://github.com/SteamClientHomebrew/Millennium/releases/tag/v3.7.0-beta.2)

## Manual opt-in

1. Obtain a compatible Millennium and Material release through the reviewed upstream sources. Confirm the installed theme's `skin.json` version and that it exposes the Matugen source-color option. Keep versioned copies of any existing theme modifications outside Git.
2. Back up the current Matugen config and any existing template and generated CSS locally. Copy [the template](millennium.css) to a regular file owned by the desktop account under its Matugen config directory. Keep the theme directory and output CSS writable only by the intended owner. Avoid symlinked output files and review the actual theme path before registering it.
3. Merge only the [example table](matugen.toml.example) into the existing Matugen config. Substitute absolute paths for the target's template and installed theme. Preserve the pre-existing ii templates and hooks.
4. Select **Matugen** as Material's source color. Let the normal ii workflow generate a palette. Confirm the generated CSS contains `--md-sys-color-primary` and check whether the installed Steam client reflects it. Follow the theme documentation if that release needs a client refresh.

To undo the adapter, remove just the added template table or restore the backed-up Matugen file after reviewing unrelated edits. Restore the previous template/generated file if applicable and choose the previous color source. Recheck paths and permissions after theme updates. This module has no lifecycle hooks or privileged installer.

## Evidence and limits

The current Matugen table resolves to the installed theme's expected output and the generated CSS contains Material roles. Repository testing renders the template with a synthetic palette in a temporary directory. The real Steam client and account data were excluded from validation. ELF64 SteamRT files and Millennium's ELF64 bootstrap were found, but loading the bootstrap in the live client, applying the palette, and switching a wallpaper with Steam open still need verification. The reference CSS was mode `0666`; tightening it to owner-write only is pending explicit local maintenance.
