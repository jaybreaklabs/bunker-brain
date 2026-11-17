#!/usr/bin/env python3
"""Bump zims.json entries to the newest Kiwix catalog release of each name+flavour.

Updates updated / size_bytes / meta4 / torrent in place and prints one line per
change. Exit 0 either way; the CI job opens a PR only if the file changed.
Stdlib only.
"""
import json
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ATOM = "{http://www.w3.org/2005/Atom}"
CATALOG = "https://opds.library.kiwix.org/catalog/v2/entries?name={}&count=50"
PATH = Path(__file__).with_name("zims.json")


def http_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "bunker-brain-manifest"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def latest(xml, name, flavour):
    """Newest catalog entry for name+flavour -> {updated, size_bytes, meta4} or None."""
    best = None
    for e in ET.fromstring(xml).iter(ATOM + "entry"):
        if e.findtext(ATOM + "name") != name or (e.findtext(ATOM + "flavour") or "") != flavour:
            continue
        link = next((l for l in e.findall(ATOM + "link") if "acquisition" in (l.get("rel") or "")), None)
        updated = (e.findtext(ATOM + "updated") or "")[:10]
        if link is not None and link.get("length") and (best is None or updated > best["updated"]):
            best = {"updated": updated, "size_bytes": int(link.get("length")), "meta4": link.get("href")}
    return best


def update(data, get=http_get):
    changes = []
    for z in data:
        try:
            new = latest(get(CATALOG.format(urllib.parse.quote(z["name"]))), z["name"], z["flavour"])
        except Exception as e:  # one bad lookup shouldn't stop the rest
            changes.append(f"skip {z['name']} {z['flavour']}: {e}")
            continue
        if not new or new["updated"] <= z["updated"] or not new["meta4"].endswith(".zim.meta4"):
            continue
        changes.append(f"{z['name']} {z['flavour']}: {z['updated']} -> {new['updated']}, "
                       f"{(new['size_bytes'] - z['size_bytes']) / 1e9:+.1f} GB")
        z.update(new, torrent=new["meta4"][:-len(".meta4")] + ".torrent")
    return changes


def main(path=PATH):
    data = json.loads(Path(path).read_text())
    for line in update(data):
        print(line)
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
