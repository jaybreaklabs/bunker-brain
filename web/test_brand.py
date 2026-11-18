"""Checks that keep the Bunker Brain design system in one piece.

Run: python3 -m unittest discover -s web -p 'test_*.py'
"""
import json
import re
import unittest
from pathlib import Path

WEB = Path(__file__).resolve().parent
ROOT = WEB.parent
PALETTE = ("bunker-olive", "field-olive", "ochre", "sand", "paper")


def palette(css):
    return {m[0]: m[1].lower() for m in re.findall(r"--bb-([a-z-]+):\s*(#[0-9a-fA-F]{3,8})\s*;", css) if m[0] in PALETTE}


class BrandTests(unittest.TestCase):
    def test_chat_palette_matches_site_tokens(self):
        site = palette((WEB / "brand/tokens.css").read_text())
        chat = palette((ROOT / "stack/chat-brand/custom.css").read_text())
        self.assertEqual(set(site), set(PALETTE))
        self.assertEqual(site, chat)

    def test_local_assets_exist_and_nothing_loads_from_the_internet(self):
        files = [WEB / "index.html", WEB / "map/index.html", WEB / "home.js", WEB / "library.js",
                 WEB / "brand/ui.js", WEB / "manifest.webmanifest"]
        for f in files:
            text = f.read_text()
            refs = re.findall(r'(?:src|href)\s*[=:]\s*"([^"]+)"', text) + re.findall(r'from\s+"([^"]+)"', text)
            for ref in refs:
                self.assertNotRegex(ref, r"^(https?:)?//", f"{f.name} loads {ref} from the internet")
                if ref.startswith("/") and not ref.startswith(("/library", "/tiles", "/links.json", "/dev/")):
                    path = ref.split("#")[0].split("?")[0]
                    if path in ("/", "/map/"):
                        continue
                    self.assertTrue((WEB / path.lstrip("/")).is_file(), f"{f.name} refers to missing {ref}")

    def test_chat_brand_mounts_exist(self):
        compose = (ROOT / "stack/compose.yaml").read_text()
        mounts = re.findall(r"\./chat-brand/([\w.-]+):/app/build/static/([\w.-]+):ro", compose)
        self.assertGreaterEqual(len(mounts), 5)
        for src, dst in mounts:
            self.assertEqual(src, dst)
            self.assertTrue((ROOT / "stack/chat-brand" / src).is_file(), src)

    def test_every_manifest_section_is_a_subject(self):
        subjects = set(re.findall(r'\{ name: "([^"]+)"', (WEB / "library.js").read_text()))
        sections = {z["section"] for z in json.loads((ROOT / "content/zims.json").read_text())}
        self.assertTrue(sections <= subjects, sections - subjects)


if __name__ == "__main__":
    unittest.main()
