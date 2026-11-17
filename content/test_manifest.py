import json
import unittest
from pathlib import Path

import check_manifest

PATH = Path(__file__).with_name("zims.json")


class ManifestTest(unittest.TestCase):
    def test_real_manifest_valid(self):
        self.assertEqual(check_manifest.problems(json.loads(PATH.read_text())), [])

    def test_detects_bad_entry(self):
        self.assertTrue(check_manifest.problems([{"name": "x"}]))


if __name__ == "__main__":
    unittest.main()
