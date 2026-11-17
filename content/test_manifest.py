import json
import unittest
from pathlib import Path

import check_manifest
import update_manifest

PATH = Path(__file__).with_name("zims.json")


class ManifestTest(unittest.TestCase):
    def test_real_manifest_valid(self):
        self.assertEqual(check_manifest.problems(json.loads(PATH.read_text())), [])

    def test_detects_bad_entry(self):
        self.assertTrue(check_manifest.problems([{"name": "x"}]))

    def test_update_bumps_only_newer(self):
        xml = (Path(__file__).parent.parent / "watcher/fixtures/kiwix_wikipedia_en_all.xml").read_bytes()
        old = {"name": "wikipedia_en_all", "flavour": "maxi", "updated": "2026-01-01", "size_bytes": 1,
               "meta4": "x.zim.meta4", "torrent": "x.zim.torrent"}
        same = dict(old, flavour="nopic", updated="2026-06-17")
        data = [old, same]
        changes = update_manifest.update(data, get=lambda url: xml)
        self.assertEqual(len(changes), 1)
        self.assertEqual(old["updated"], "2026-08-25")
        self.assertEqual(old["size_bytes"], 127418088448)
        self.assertTrue(old["torrent"].endswith("wikipedia_en_all_maxi_2026-08.zim.torrent"))
        self.assertEqual(same["updated"], "2026-06-17")


if __name__ == "__main__":
    unittest.main()
