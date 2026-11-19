"""Offline tests for the three aria2 list builders."""
import base64
import gzip
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build_lists


class BuildListsTest(unittest.TestCase):
    def test_library_skips_files_already_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = Path(tmp) / "content"
            content.mkdir()
            (content / "zims.json").write_text(json.dumps([
                {"name": "wikivoyage_en_all", "torrent": "https://example.com/have.torrent",
                 "size_bytes": 10},
                {"name": "wikipedia_en_all", "torrent": "https://example.com/new.torrent",
                 "size_bytes": 2_000_000_000},
            ]))
            with patch.object(build_lists, "ROOT", Path(tmp) / "fetch"):
                lines, total, notes = build_lists.library()

        self.assertEqual(lines, ["https://example.com/new.torrent", "  dir=/library/incoming",
                                 "  follow-torrent=mem", "  seed-time=0"])
        self.assertEqual(total, 2_000_000_000)
        self.assertEqual(notes, [])

    def test_maps_parses_latest_build_and_gzipped_osmand_regions(self):
        builds = [{"key": "old.pmtiles", "md5sum": base64.b64encode(b"0" * 16).decode(),
                   "size": 1},
                  {"key": "new.pmtiles", "md5sum": base64.b64encode(bytes(range(16))).decode(),
                   "size": 2_000_000_000}]
        regions = gzip.compress(b'<indexes><region type="map" name="world.obf.zip" '
                                b'containerSize="300"/><region type="voice" name="voice.zip" '
                                b'containerSize="400"/></indexes>')
        responses = {"https://build-metadata.protomaps.dev/builds.json": json.dumps(builds).encode(),
                     "https://download.osmand.net/get_indexes?gzip=true": regions}
        with patch.object(build_lists, "get",
                          side_effect=lambda url, timeout=60: responses[url]) as fetch:
            lines, total, notes = build_lists.maps()

        self.assertEqual(fetch.call_count, 2)
        self.assertEqual(lines, [
            "https://build.protomaps.com/new.pmtiles", "  dir=/library/incoming",
            "  out=planet.pmtiles", "  checksum=md5=000102030405060708090a0b0c0d0e0f",
            "  split=16", "  max-connection-per-server=16",
            "https://download.osmand.net/download?standard=yes&file=world.obf.zip",
            "  dir=/library/phone-maps/osmand", "  out=world.obf.zip",
        ])
        self.assertEqual(total, 2_000_000_300)
        self.assertEqual(notes, ["Protomaps new.pmtiles 2.0 GB; OsmAnd 1 world map files"])

    def test_models_selects_weights_and_sidecars_with_nested_paths(self):
        repo = "example/model"
        tree = [
            {"type": "file", "path": "weights/model-Q4_K_M.gguf",
             "lfs": {"size": 2_000_000_000, "oid": "a" * 64}},
            {"type": "file", "path": "weights/config.json", "size": 100},
            {"type": "file", "path": "weights/model-Q8_0.gguf",
             "lfs": {"size": 3_000_000_000, "oid": "b" * 64}},
            {"type": "directory", "path": "weights/Q4_K_M", "size": 0},
        ]
        with patch.object(build_lists, "MODELS", [("example", repo, r"Q4_K_M")]), \
             patch.object(build_lists, "get", return_value=json.dumps(tree).encode()) as fetch:
            lines, total, notes = build_lists.models()

        fetch.assert_called_once_with(
            "https://huggingface.co/api/models/example/model/tree/main?recursive=1")
        self.assertEqual(lines, [
            "https://huggingface.co/example/model/resolve/main/weights/model-Q4_K_M.gguf",
            "  dir=/models/models/example/weights", "  out=model-Q4_K_M.gguf",
            f"  checksum=sha-256={'a' * 64}",
            "https://huggingface.co/example/model/resolve/main/weights/config.json",
            "  dir=/models/models/example/weights", "  out=config.json",
        ])
        self.assertEqual(total, 2_000_000_100)
        self.assertEqual(notes, [f"{'example':45} example/model  2.0 GB"])


if __name__ == "__main__":
    unittest.main()
