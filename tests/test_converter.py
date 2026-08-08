import os
import tempfile
import time
import unittest
from pathlib import Path

from converter import find_latest_file, resolve_output_root


class ConverterTests(unittest.TestCase):
    def test_resolve_output_root_uses_export_folder(self):
        root = resolve_output_root(None)
        expected = Path(__file__).resolve().parents[1] / "export mp3 or mp4"
        self.assertEqual(root, expected)

    def test_find_latest_file_returns_most_recent_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            first = Path(temp_dir) / "first.mp3"
            second = Path(temp_dir) / "second.mp3"
            first.write_text("old", encoding="utf-8")
            second.write_text("new", encoding="utf-8")
            old_time = time.time() - 60
            new_time = time.time()
            os.utime(first, (old_time, old_time))
            os.utime(second, (new_time, new_time))

            self.assertEqual(find_latest_file(Path(temp_dir)), second)


if __name__ == "__main__":
    unittest.main()
