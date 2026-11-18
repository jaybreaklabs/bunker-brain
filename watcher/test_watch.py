"""Tests for watch.py against saved (trimmed) real responses. No network."""
import datetime as dt
import json
import unittest
import urllib.error
from pathlib import Path

import watch

FIX = Path(__file__).resolve().parent / "fixtures"
NOW = dt.datetime(2026, 11, 17, 12, 0, tzinfo=dt.timezone.utc)
CFG = {"sources": [
    {"id": "kiwix", "type": "kiwix", "group": "Library", "zims_file": "/nonexistent/zims.json",
     "default_zims": [["wikipedia_en_all", "maxi"], ["wikipedia_en_all", "nopic"]]},
    {"id": "protomaps", "type": "protomaps", "group": "Maps", "url": "https://pm/builds.json"},
    {"id": "osmand", "type": "osmand", "group": "Maps", "url": "https://osmand/idx",
     "groups": {"OsmAnd US maps": "^Us_.*\\.obf\\.zip$", "OsmAnd world maps": "\\.obf\\.zip$"}},
    {"id": "huggingface", "type": "huggingface", "group": "Models", "exclude": "(?i)-FP8$",
     "orgs": ["Qwen"]},
    {"id": "runtimes", "type": "github", "group": "Runtimes", "repos": ["ggml-org/llama.cpp"]},
]}


def fixtures():
    return {
        "opds.library.kiwix.org": (FIX / "kiwix_wikipedia_en_all.xml").read_bytes(),
        "https://pm/builds.json": (FIX / "protomaps_builds.json").read_bytes(),
        "https://osmand/idx": (FIX / "osmand_indexes.xml.gz").read_bytes(),
        "huggingface.co": (FIX / "hf_qwen.json").read_bytes(),
        "ggml-org/llama.cpp": (FIX / "github_llama_cpp.json").read_bytes(),
    }


def getter(responses):
    def get(url):
        for part, body in responses.items():
            if part in url:
                if isinstance(body, Exception):
                    raise body
                return watch.gzip.decompress(body) if body[:2] == b"\x1f\x8b" else body
        raise AssertionError(f"unexpected URL {url}")
    return get


def baseline_state():
    return watch.run(CFG, {}, getter(fixtures()), {}, NOW)[2]


class WatchTest(unittest.TestCase):
    def test_first_run_records_baseline(self):
        title, body, state = watch.run(CFG, {}, getter(fixtures()), {"bunker-brain": 410e9}, NOW)
        self.assertIn("baseline recorded", title)
        self.assertIn("recorded 7 items from 5 sources", body)
        self.assertNotIn("→", body)
        self.assertEqual(state["kiwix"]["wikipedia_en_all maxi"]["d"], "2026-08")
        self.assertEqual(state["runtimes"]["ggml-org/llama.cpp"]["v"], "v1.0.0")
        self.assertIn("Free: bunker-brain 410.0 GB", body)

    def test_no_changes(self):
        title, body, _ = watch.run(CFG, baseline_state(), getter(fixtures()), {}, NOW)
        self.assertIn("no changes", title)
        self.assertEqual(body, "No changes since 2026-11-17.")

    def test_changes_are_grouped_with_size_delta(self):
        state = baseline_state()
        resp = fixtures()
        resp["opds.library.kiwix.org"] = (resp["opds.library.kiwix.org"]
                                          .replace(b"2026-08-25T00:00:00Z", b"2026-11-20T00:00:00Z")
                                          .replace(b'length="127', b'length="128'))
        builds = json.loads(resp["https://pm/builds.json"])
        builds.append({"key": "20261215.pmtiles", "size": builds[-1]["size"] - 2_000_000_000})
        resp["https://pm/builds.json"] = json.dumps(builds).encode()
        resp["ggml-org/llama.cpp"] = b'{"tag_name": "v1.1.0"}'
        models = json.loads(resp["huggingface.co"])
        models[:0] = [{"id": "Qwen/Qwen4-8B", "createdAt": "2026-11-15T00:00:00.000Z"},
                      {"id": "Qwen/Qwen4-8B-FP8", "createdAt": "2026-11-15T00:00:01.000Z"}]
        resp["huggingface.co"] = json.dumps(models).encode()

        title, body, new_state = watch.run(CFG, state, getter(resp), {}, NOW)
        self.assertIn("4 updates", title)
        self.assertIn("Library\n- wikipedia_en_all maxi 2026-08 → 2026-11, +1.0 GB", body)
        self.assertIn("Protomaps planet 20261116 → 20261215, -2.0 GB", body)
        self.assertIn("Models\n- Qwen: 1 new: Qwen4-8B", body)  # FP8 excluded by regex
        self.assertIn("Runtimes\n- ggml-org/llama.cpp v1.0.0 → v1.1.0", body)
        self.assertLess(body.index("Library"), body.index("Maps"))
        self.assertEqual(new_state["runtimes"]["ggml-org/llama.cpp"]["v"], "v1.1.0")

    def test_failing_source_is_reported_and_keeps_old_state(self):
        state = baseline_state()
        resp = fixtures()
        resp["https://pm/builds.json"] = urllib.error.URLError("timed out")
        resp["ggml-org/llama.cpp"] = urllib.error.HTTPError("u", 403, "rate limited", {}, None)
        title, body, new_state = watch.run(CFG, state, getter(resp), {}, NOW)
        self.assertIn("no changes", title)
        self.assertIn("- protomaps: failed: unreachable (timed out)", body)
        self.assertIn("- runtimes: GitHub rate limit hit at ggml-org/llama.cpp", body)
        self.assertEqual(new_state["protomaps"], state["protomaps"])
        self.assertEqual(new_state["runtimes"], state["runtimes"])

    def test_missing_items_are_noted(self):
        cfg = json.loads(json.dumps(CFG))
        cfg["sources"][2]["groups"]["OsmAnd Texas"] = "^Us_texas_northamerica_2"  # deleted_map only
        _, body, _ = watch.run(cfg, {}, getter(fixtures()), {}, NOW)
        self.assertIn("osmand: OsmAnd Texas: no files match", body)

    def test_body_is_capped(self):
        state = baseline_state()
        resp = fixtures()
        long_ids = [{"id": f"Qwen/{'x' * 9000}-{i}", "createdAt": "2026-11-16T00:00:00.000Z"} for i in range(8)]
        resp["huggingface.co"] = json.dumps(long_ids).encode()
        _, body, _ = watch.run(CFG, state, getter(resp), {}, NOW)
        self.assertLessEqual(len(body.encode()), watch.MAX_BODY_BYTES + 20)

    def test_env_file_and_overrides(self):
        import os
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".env", delete=False) as f:
            f.write("# comment\nexport WATCHER_ALERT_URL='http://192.0.2.20/alert'\nWATCHER_ALERT_SECRET=a\n")
        os.environ["WATCHER_ALERT_SECRET"] = "b"
        try:
            env = watch.load_env(f.name)
        finally:
            del os.environ["WATCHER_ALERT_SECRET"]
            os.unlink(f.name)
        self.assertEqual(env["WATCHER_ALERT_URL"], "http://192.0.2.20/alert")
        self.assertEqual(env["WATCHER_ALERT_SECRET"], "b")  # real env wins
        self.assertEqual(set(watch.free_space(f"here={FIX},gone=/nonexistent")), {"here"})


if __name__ == "__main__":
    unittest.main()
