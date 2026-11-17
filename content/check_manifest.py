#!/usr/bin/env python3
"""Validate zims.json and print per-section and grand totals (GB)."""
import json, re, sys
from collections import defaultdict
from pathlib import Path

SECTIONS = {"Reference", "Medical", "Water & Food", "Repair & Build",
            "Power & Energy", "Preparedness", "Learning"}
STR = ("name", "flavour", "title", "section", "updated", "meta4", "torrent")


def problems(data):
    if not isinstance(data, list):
        return ["top level must be a list"]
    errs, seen = [], set()
    for i, z in enumerate(data):
        w = f"#{i} {z.get('name') if isinstance(z, dict) else z!r}"
        if not isinstance(z, dict):
            errs.append(f"{w}: not an object"); continue
        for k in STR:
            if not isinstance(z.get(k), str) or (k != "flavour" and not z[k]):
                errs.append(f"{w}: {k} must be a string" + ("" if k == "flavour" else " (non-empty)"))
        if not isinstance(z.get("priority"), int) or not 1 <= z["priority"] <= 9:
            errs.append(f"{w}: priority must be int 1-9")
        s = z.get("size_bytes")
        if not isinstance(s, int) or isinstance(s, bool) or s <= 0:
            errs.append(f"{w}: size_bytes must be positive int")
        if z.get("section") not in SECTIONS:
            errs.append(f"{w}: bad section {z.get('section')!r}")
        if not re.fullmatch(r"\d{4}-\d\d-\d\d", str(z.get("updated"))):
            errs.append(f"{w}: updated must be YYYY-MM-DD")
        m, t = str(z.get("meta4")), str(z.get("torrent"))
        if not m.startswith("https://") or not m.endswith(".zim.meta4"):
            errs.append(f"{w}: meta4 must be https URL ending .zim.meta4")
        if t != m[:-len(".meta4")] + ".torrent":
            errs.append(f"{w}: torrent must be meta4 with .meta4 -> .torrent")
        key = (z.get("name"), z.get("flavour"))
        if key in seen:
            errs.append(f"{w}: duplicate name+flavour")
        seen.add(key)
    return errs


def main(path):
    data = json.loads(Path(path).read_text())
    errs = problems(data)
    for e in errs:
        print("ERROR", e, file=sys.stderr)
    if errs:
        return 1
    tot = defaultdict(int)
    for z in data:
        tot[z["section"]] += z["size_bytes"]
    for s in sorted(tot):
        print(f"{s:16} {tot[s] / 1e9:8.1f} GB")
    print(f"{'TOTAL':16} {sum(tot.values()) / 1e9:8.1f} GB  ({len(data)} ZIMs)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).with_name("zims.json")))
