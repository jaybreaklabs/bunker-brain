import asyncio
import os
import unittest
from pathlib import Path
from unittest import mock

import kiwix_search as k

FIX = Path(__file__).parent / "fixtures"


def fixture(name):
    return (FIX / name).read_text(encoding="utf-8")


class ParseTests(unittest.TestCase):
    def test_parse_search(self):
        hits = k.parse_search(fixture("search_boil_water.xml"))
        self.assertEqual(len(hits), 3)
        self.assertEqual(hits[0]["title"], "Water")
        self.assertEqual(hits[0]["link"], "/content/wikivoyage_en_all_nopic_2026-09/Water")
        self.assertEqual(hits[0]["book"], "Wikivoyage")
        self.assertEqual(hits[0]["book_name"], "wikivoyage_en_all_nopic_2026-09")
        self.assertIn("drinking water", hits[0]["snippet"])  # <b> tags flattened
        self.assertNotIn("<b>", hits[0]["snippet"])

    def test_parse_search_empty(self):
        self.assertEqual(k.parse_search(fixture("search_empty.xml")), [])

    def test_parse_catalog(self):
        names = {b["name"]: b["title"] for b in k.parse_catalog(fixture("catalog_entries.xml"))}
        self.assertEqual(names["wikivoyage_en_all"], "Wikivoyage")
        self.assertEqual(names["zimgit-water_en"], "Water Treatment Library")

    def test_html_to_text(self):
        text = k.html_to_text(fixture("article_water.html"))
        self.assertIn("unboiled tap water is dangerous to drink", text)
        self.assertNotIn("RLCONF", text)  # script dropped
        self.assertNotIn("<", text)
        self.assertNotIn("  ", text)

    def test_trim(self):
        self.assertEqual(k.trim("short", 10), "short")
        out = k.trim("word " * 100, 50)
        self.assertLessEqual(len(out), 54)
        self.assertTrue(out.endswith(" ..."))

    def test_public_url(self):
        t = k.Tools()
        self.assertEqual(t._public_url("/content/b/A"), "https://wiki.example.com/library/content/b/A")
        t.valves.KIWIX_BASE_URL = "http://nas:8790/library"
        self.assertEqual(t._public_url("/library/content/b/A"), "https://wiki.example.com/library/content/b/A")


class ToolTests(unittest.TestCase):
    def test_search_formats_and_emits(self):
        pages = {"search": fixture("search_boil_water.xml"), "content": fixture("article_water.html")}
        events = []

        async def emit(e):
            events.append(e)

        t = k.Tools()
        t.valves.MAX_RESULTS = 2
        t.valves.MAX_CHARS_PER_ARTICLE = 200
        with mock.patch.object(k, "_get", lambda url: pages["search" if "/search?" in url else "content"]):
            out = asyncio.run(t.search_library("boil water", __event_emitter__=emit))
        self.assertIn("cite them inline as [n]", out)
        self.assertIn("[1] Water (Wikivoyage)", out)
        self.assertIn("URL: https://wiki.example.com/library/content/wikivoyage_en_all_nopic_2026-09/Water", out)
        self.assertNotIn("[3]", out)
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["type"], "citation")

    def test_unreachable(self):
        t = k.Tools()
        t.valves.KIWIX_BASE_URL = "http://127.0.0.1:9"  # discard port: connection refused
        out = asyncio.run(t.search_library("boil water"))
        self.assertIn("could not be reached", out)
        self.assertIn("could not be reached", asyncio.run(t.list_books()))

    def test_no_results(self):
        with mock.patch.object(k, "_get", lambda url: fixture("search_empty.xml")):
            out = asyncio.run(k.Tools().search_library("zzqq"))
        self.assertIn("no results", out)


@unittest.skipUnless(os.environ.get("KIWIX_LIVE") == "1", "set KIWIX_LIVE=1 to hit the live kiwix-serve")
class LiveTests(unittest.TestCase):
    def test_live(self):
        t = k.Tools()
        if os.environ.get("KIWIX_BASE_URL"):
            t.valves.KIWIX_BASE_URL = os.environ["KIWIX_BASE_URL"]
        books = asyncio.run(t.list_books())
        self.assertIn("wikivoyage", books)
        out = asyncio.run(t.search_library("boil water"))
        print("\n" + out[:1500])
        self.assertIn("[1] ", out)
        self.assertIn("URL: https://wiki.example.com/library/content/", out)


if __name__ == "__main__":
    unittest.main()
