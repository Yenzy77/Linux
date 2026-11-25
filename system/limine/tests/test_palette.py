import unittest

import palette

class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.config = b"""timeout: 3
wallpaper: boot():/ii-limine-theme/wallpaper.qoi
wallpaper_style: stretched
term_margin_gradient: 64
term_foreground: ffffff
term_background: ee252535
term_foreground_bright: ffffff
term_background_bright: ee272737
interface_help_colour: ffffff
interface_help_colour_bright: ffffff

/+CachyOS
  //Synthetic kernel
  protocol: linux
  cmdline: fixture-only
"""
        self.roles = dict(primary="#ffb2ba", on_primary="#561d27", secondary="#e7bdc1",
                          on_surface="#f0dedf", on_surface_variant="#d7c1c3")
    def test_only_header_colors_change(self):
        colors = palette.from_matugen(self.roles)
        original, updated = self.config, palette.patch_config(self.config, colors)
        self.assertNotEqual(original, updated)
        self.assertEqual(original.split(b"\n/+CachyOS")[1], updated.split(b"\n/+CachyOS")[1])
        self.assertEqual(palette.patch_config(updated, colors), updated)
        self.assertEqual(palette.config_colors(updated), colors)
    def test_reject_injection_and_config_ambiguity(self):
        colors = palette.from_matugen(self.roles)
        with self.assertRaises(ValueError):
            palette.patch_config(self.config, (*colors[:-1], "000000\ncmdline:"))
        with self.assertRaises(ValueError):
            palette.patch_config(b"term_foreground: ffffff\n" + self.config, colors)
    def test_dark_foreground_is_adjusted(self):
        roles = {key: "#121319" for key in self.roles}
        colors = palette.from_matugen(roles)
        for index in (0, 2, 4, 5):
            self.assertGreaterEqual(palette.contrast(colors[index], "525252"), 4.5)

if __name__ == "__main__":
    unittest.main()
