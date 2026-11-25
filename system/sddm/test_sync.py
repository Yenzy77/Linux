import io
import json
import tempfile
import unittest
from pathlib import Path

import sync


class SyncTests(unittest.TestCase):
    def test_paths_reject_parent_traversal_and_links(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "still.png").write_bytes(b"image")
            (root / "alias.png").symlink_to("still.png")
            (root / "alias-dir").symlink_to(root, target_is_directory=True)
            with sync.open_local(str(root / "still.png")) as stream:
                self.assertEqual(stream.read(), b"image")
            for path in ("alias.png", "alias-dir/still.png", "../still.png"):
                with self.subTest(path=path), self.assertRaises((OSError, ValueError)):
                    sync.open_local(str(root / path))

    def test_receiver_rejects_unknown_or_active_config(self):
        for values in ({"Background": "/etc/passwd"},
                       {"IISetting_panelFamily": "../test"},
                       {"IIColor_primary": "#123456\nBackground=oops"}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                sync.validate(values)

    def test_receiver_keeps_last_good_generation_on_bad_media(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)
            frame = b"\xff\xd8\xff\xe0sample\xff\xd9"
            values = {"IIColor_primary": "#112233", "IISetting_panelFamily": "ii",
                      "IISetting_background_widgets_clock_quote_text": "a=\n# b"}
            self.publish(state, frame, values)
            cfg = state / "theme.conf.user"
            first = cfg.read_bytes()
            self.assertIn(b"IIColor_primary=#112233", first)
            self.assertIn(b"Background=file:", first)
            self.assertNotIn(b"\n# b", first)
            with self.assertRaises(ValueError):
                self.publish(state, b"plain text", values)
            self.assertEqual(cfg.read_bytes(), first)
            self.publish(state, frame, {**values, "IIColor_primary": "#445566"})
            self.assertIn(b"IIColor_primary=#445566", cfg.read_bytes())
            self.assertNotEqual(first, cfg.read_bytes())

    @staticmethod
    def publish(state, image, values):
        header = json.dumps({"values": values, "image": len(image), "video": 0}).encode()
        return sync.publish(io.BytesIO(header + b"\n" + image), state)


if __name__ == "__main__":
    unittest.main()
