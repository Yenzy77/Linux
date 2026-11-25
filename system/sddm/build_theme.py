import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sync

source, dest = (Path(arg).resolve() for arg in sys.argv[1:])
dest.mkdir()
for directory in ("Assets", "Backgrounds", "Components"):
    shutil.copytree(source / directory, dest / directory, ignore=shutil.ignore_patterns(
        ".gitignore", "example.qml", "README.md"))
for name in ("LICENSE", "Main.qml", "metadata.desktop"):
    shutil.copyfile(source / name, dest / name)
(dest / "Themes").mkdir()
shutil.copyfile(source / "iiMatugen/ii-sddm.conf", dest / "Themes/ii-sddm.conf")
fonts = source / "fonts/ii-sddm-theme-fonts/FluentuiSystemIcons"
google_fonts = fonts.parent / "GooglSansFlex"
(dest / "Fonts").mkdir()
shutil.copyfile(fonts / "FluentSystemIcons-Regular.ttf", dest / "Fonts/FluentSystemIcons-Regular.ttf")
google_font = next(google_fonts.glob("*.ttf"))
shutil.copyfile(google_font, dest / "Fonts/GoogleSansFlex.ttf")
shutil.copyfile(google_fonts / "LICENSE", dest / "Fonts/GoogleSansFlex.LICENSE")
for name in ("LICENSE", "NOTICE"):
    shutil.copyfile(fonts / name, dest / "Fonts" / name)

settings = (source / "iiMatugen/Settings.qml").read_text().splitlines()
settings = [line for line in settings if not line.startswith("//")]
for name, kind, default in [
    ("background_widgets_clock_digital_adaptiveAlignment", "bool", "false"),
    ("lock_blur_radius", "real", "100"),
    ("appearance_fonts_main", "string", '"Google Sans Flex"'),
    ("appearance_fonts_expressive", "string", '"Space Grotesk"'),
    ("appearance_fonts_reading", "string", '"Readex Pro"'),
    ("appearance_transparency_enable", "bool", "true"),
    ("appearance_transparency_contentTransparency", "real", "0.57"),
    ("appearance_transparency_backgroundTransparency", "real", "0"),
]:
    settings.insert(-1, f"    property {kind} {name}: {default}")

accessors = r'''
    property var syncConfig: null

    function text(name, fallback) {
        const value = syncConfig ? String(syncConfig["IISetting_" + name] ?? "") : "";
        if (!/^hex_(?:[a-f0-9]{2})*$/.test(value)) return fallback;
        try {
            return decodeURIComponent(value.slice(4).replace(/../g, "%$&"));
        } catch (error) {
            return fallback;
        }
    }

    function flag(name, fallback) {
        const value = syncConfig ? String(syncConfig["IISetting_" + name] ?? "") : "";
        return value === "true" ? true : value === "false" ? false : fallback;
    }

    function number(name, fallback) {
        const value = syncConfig ? String(syncConfig["IISetting_" + name] ?? "") : "";
        return value !== "" && Number.isFinite(Number(value)) ? Number(value) : fallback;
    }
'''
read_type = {"string": "text", "bool": "flag", "int": "number", "real": "number"}
for index, line in enumerate(settings):
    match = re.fullmatch(r"    property (\w+) (\w+): (.*?)(?:\s+//.*)?", line.strip("\r"))
    if not match:
        continue
    kind, key, fallback = match.groups()
    assert "IISetting_" + key in sync.SETTING_RULES, key
    settings[index] = f'    readonly property {kind} {key}: {read_type[kind]}("{key}", {fallback.strip()})'
settings.insert(-1, accessors)
(dest / "Components/Settings.qml").write_text("\n".join(settings) + "\n")

colors = (source / "iiMatugen/Colors.qml").read_text()
colors = colors.replace("// Don't edit this file or the script won't pick up the right background\n"
                        "// ~/.config/ii-sddm-theme/default-background/background.png\n", "")
colors = colors.replace("QtObject {", '''QtObject {
    property var syncConfig: null

    function palette(name, fallback) {
        const value = syncConfig ? String(syncConfig["IIColor_" + name] ?? "") : "";
        return /^#[a-fA-F0-9]{6}$/.test(value) ? value : fallback;
    }''', 1)
for color in sync.COLORS:
    colors, count = re.subn(r'(property color ' + color + r': )"(#[a-f0-9]{6})"',
                            rf'\1palette("{color}", "\2")', colors)
    assert count == 1, color
colors = colors.replace("property real contentTransparency: 0.57",
    "property real contentTransparency: Settings.appearance_transparency_enable ? "
    "Settings.appearance_transparency_contentTransparency : 0")
colors = colors.replace("property real backgroundTransparency: 0",
    "property real backgroundTransparency: Settings.appearance_transparency_enable ? "
    "Settings.appearance_transparency_backgroundTransparency : 0")
(dest / "Components/Colors.qml").write_text(colors)

appearance = dest / "Components/Appearance.qml"
content = appearance.read_text().replace('font_family_main: "Google Sans Flex"',
    "font_family_main: Settings.appearance_fonts_main").replace('font_family_expressive: "Space Grotesk"',
    "font_family_expressive: Settings.appearance_fonts_expressive").replace('font_family_reading: "Readex Pro"',
    "font_family_reading: Settings.appearance_fonts_reading")
content = content.replace('    property string animfont:', """    property FontLoader googleSans: FontLoader {
        source: "../Fonts/GoogleSansFlex.ttf"
    }
    property string animfont:""")
content = content.replace('    property string waffleIconFont: "FluentSystemIcons-Regular"',
    '''    property FontLoader waffleIcons: FontLoader {
        source: "../Fonts/FluentSystemIcons-Regular.ttf"
    }
    property string waffleIconFont: waffleIcons.name || "FluentSystemIcons-Regular"''')
appearance.write_text(content)

main = dest / "Main.qml"
content = main.read_text()
content = content.replace("    readonly property variant screenGeometry: screenModel.geometry(screenModel.primary)\n\n", "")
content = content.replace("    x: screenGeometry.x || 0\n    y: screenGeometry.y || 0", """    Component.onCompleted: {
        Settings.syncConfig = config;
        Colors.syncConfig = config;
    }""")
content = content.replace("                return 100;", "                return Settings.lock_blur_radius;")
main.write_text(content)

metadata = dest / "metadata.desktop"
metadata.write_text(metadata.read_text().replace("Screenshot=Previews/preview1.png\n", ""))
(dest / "UPSTREAM-COMMIT").write_text("1d4bcb66647f750bcc14d73de025eae8dd1e3db7\n")
