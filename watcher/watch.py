#!/usr/bin/env python3
"""Monthly release watcher for the offline library (stdlib only, notify-only).

Checks each source in sources.json, diffs against the saved state, posts one
digest to a webhook (WATCHER_ALERT_URL), then saves the new state. See README.md.
"""
import argparse
import datetime as dt
import gzip
import json
import os
import re
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_STATE = "watcher-state.json"
UA = "offline-library-watcher/1.0"
MAX_BODY_BYTES = 55_000  # receiver rejects requests over 64 KiB; leave room for the envelope
GROUPS = ["Library", "Maps", "Models", "Runtimes"]
ATOM = "{http://www.w3.org/2005/Atom}"
KIWIX_URL = "https://opds.library.kiwix.org/catalog/v2/entries?name={}&count=20"
HF_URL = "https://huggingface.co/api/models?author={}&sort=createdAt&direction=-1&limit=20"
GH_URL = "https://api.github.com/repos/{}/releases/latest"
HF_LIST_MAX = 10


def http_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    return gzip.decompress(data) if data[:2] == b"\x1f\x8b" else data


def err(e):
    if isinstance(e, urllib.error.HTTPError):
        return f"HTTP {e.code}"
    if isinstance(e, urllib.error.URLError):
        return f"unreachable ({e.reason})"
    return f"{type(e).__name__}: {e}"[:200]


def gb(n):
    return f"{n / 1e12:.2f} TB" if abs(n) >= 1e12 else f"{n / 1e9:.1f} GB"


# --- sources: each returns (items, notes); item = {"v": compare, "d": display, "size": bytes?}

def kiwix_targets(src):
    path = HERE / src.get("zims_file", "../content/zims.json")
    if path.exists():
        pairs = [(z["name"], z.get("flavour") or "") for z in json.loads(path.read_text())]
    else:
        pairs = [tuple(p) for p in src["default_zims"]]
    targets = {}
    for name, flavour in pairs:
        targets.setdefault(name, set()).add(flavour)
    return targets


def check_kiwix(src, get):
    items, notes = {}, []
    for name, flavours in kiwix_targets(src).items():
        try:
            root = ET.fromstring(get(KIWIX_URL.format(urllib.parse.quote(name))))
        except Exception as e:
            notes.append(f"{name}: {err(e)}")
            continue
        found = {}
        for entry in root.iter(ATOM + "entry"):
            if entry.findtext(ATOM + "name") != name:
                continue
            flavour = entry.findtext(ATOM + "flavour") or ""
            updated = entry.findtext(ATOM + "updated") or ""
            if flavour in flavours and updated > found.get(flavour, ("",))[0]:
                length = next((link.get("length") for link in entry.findall(ATOM + "link")
                               if "acquisition" in (link.get("rel") or "")), None)
                found[flavour] = (updated, int(length) if length else None)
        for flavour in sorted(flavours):
            label = f"{name} {flavour}".strip()
            if flavour not in found:
                notes.append(f"{label}: not in catalog")
                continue
            updated, size = found[flavour]
            items[label] = {"v": updated, "d": updated[:7], "size": size}
    return items, notes


def check_protomaps(src, get):
    b = max(json.loads(get(src["url"])), key=lambda b: b["key"])
    return {"Protomaps planet": {"v": b["key"], "d": b["key"].split(".")[0], "size": b.get("size")}}, []


def check_osmand(src, get):
    # One line per map set (e.g. all US maps), not per file: OsmAnd republishes every
    # region together each month, so the newest timestamp and total size say it all.
    regions = [r for r in ET.fromstring(get(src["url"])).iter("region") if r.get("type") == "map"]
    items, notes = {}, []
    for label, pattern in src["groups"].items():
        hits = [r for r in regions if re.search(pattern, r.get("name", ""))]
        if not hits:
            notes.append(f"{label}: no files match {pattern}")
            continue
        newest = max(hits, key=lambda r: int(r.get("timestamp") or 0))
        items[label] = {"v": newest.get("timestamp"), "d": newest.get("date"),
                        "size": sum(int(r.get("containerSize") or 0) for r in hits)}
    return items, notes


def check_github(src, get):
    items, notes = {}, []
    for repo in src["repos"]:
        try:
            tag = json.loads(get(GH_URL.format(repo)))["tag_name"]
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                notes.append(f"GitHub rate limit hit at {repo}; skipped the rest this run")
                break
            notes.append(f"{repo}: {err(e)}")
            continue
        except Exception as e:
            notes.append(f"{repo}: {err(e)}")
            continue
        items[repo] = {"v": tag, "d": tag}
    return items, notes


def check_hf(src, get):
    items, notes = {}, []
    for org in src["orgs"]:
        org = {"name": org} if isinstance(org, str) else org
        inc = org.get("include")
        exc = org.get("exclude", src.get("exclude"))
        try:
            models = json.loads(get(HF_URL.format(urllib.parse.quote(org["name"]))))
        except Exception as e:
            notes.append(f"{org['name']}: {err(e)}")
            continue
        if not models:
            notes.append(f"{org['name']}: no models returned")
            continue
        created = [m["createdAt"] for m in models]
        repos = [[m["id"], m["createdAt"]] for m in models
                 if (not inc or re.search(inc, m["id"])) and not (exc and re.search(exc, m["id"]))]
        items[org["name"]] = {"v": max(created), "d": max(created)[:10],
                              "oldest": min(created), "repos": repos}
    return items, notes


CHECKS = {"kiwix": check_kiwix, "protomaps": check_protomaps, "osmand": check_osmand,
          "github": check_github, "huggingface": check_hf}


# --- diff and digest

def change_line(key, new, old):
    if "repos" in new:  # Hugging Face org: list repos created since the last run
        fresh = [rid.split("/", 1)[-1] for rid, created in new["repos"] if created > old["v"]]
        if not fresh:
            return None
        more = f", +{len(fresh) - HF_LIST_MAX} more" if len(fresh) > HF_LIST_MAX else ""
        full = " (page full, there may be more)" if new["oldest"] > old["v"] else ""
        return f"{key}: {len(fresh)} new: {', '.join(fresh[:HF_LIST_MAX])}{more}{full}"
    if old["v"] == new["v"]:
        return None
    line = f"{key} {old['d']} → {new['d']}"
    if new.get("size") is not None:
        delta = new["size"] - old["size"] if old.get("size") is not None else None
        line += f", {'+' if delta >= 0 else '-'}{gb(abs(delta))}" if delta is not None else f", {gb(new['size'])}"
    return line


def run(cfg, old_state, get, free, now):
    """Check every source; return (title, body, new_state)."""
    first_run = not any(k for k in old_state if not k.startswith("_"))
    new_state = dict(old_state)
    groups, problems, baselined = {}, [], []
    tracked = 0
    for src in cfg["sources"]:
        sid = src["id"]
        try:
            items, notes = CHECKS[src["type"]](src, get)
        except Exception as e:
            items, notes = {}, [f"failed: {err(e)}"]
        problems += [f"{sid}: {n}" for n in notes]
        prev = old_state.get(sid)
        if prev is None and not items:
            continue  # nothing to baseline yet; try again next run
        merged = dict(prev or {})  # items that failed this run keep their last-seen value
        for key, item in items.items():
            merged[key] = {k: item[k] for k in ("v", "d", "size") if item.get(k) is not None}
            if prev is None:
                continue
            if key not in prev:
                line = f"{key}: now tracked at {item['d']}"
            else:
                line = change_line(key, item, prev[key])
            if line:
                groups.setdefault(src.get("group", "Other"), []).append(line)
        if prev is None:
            baselined.append(sid)
        tracked += len(items)
        new_state[sid] = merged
    new_state["_meta"] = {"last_run": now.isoformat(timespec="seconds")}

    month = now.strftime("%Y-%m")
    free_line = "Free: " + ", ".join(f"{k} {gb(v)}" for k, v in free.items()) if free else ""
    problem_block = "\n".join(["Problems:"] + [f"- {p}" for p in problems]) if problems else ""
    changes = sum(len(v) for v in groups.values())
    if first_run:
        title = f"Offline library watcher: baseline recorded ({month})"
        parts = [f"First run: recorded {tracked} items from {len(baselined)} sources. "
                 "Later runs report changes against this baseline.", free_line, problem_block]
    elif not changes:
        since = old_state.get("_meta", {}).get("last_run", "?")[:10]
        title = f"Offline library: no changes ({month})"
        parts = [f"No changes since {since}." + (f" {free_line}." if free_line else ""), problem_block]
    else:
        title = f"Offline library: {changes} update{'s' if changes != 1 else ''} ({month})"
        parts = ["\n".join([g] + [f"- {l}" for l in groups[g]])
                 for g in GROUPS + sorted(set(groups) - set(GROUPS)) if g in groups]
        parts += [free_line, problem_block]
    if baselined and not first_run:
        parts.append("Baseline recorded for new sources: " + ", ".join(baselined))
    body = "\n\n".join(p for p in parts if p)
    raw = body.encode()
    if len(raw) > MAX_BODY_BYTES:
        body = raw[:MAX_BODY_BYTES].decode(errors="ignore") + "\n… (truncated)"
    return title, body, new_state


# --- I/O

def free_space(spec):
    """spec: "name=/path,name=/path" (WATCHER_FREE_PATHS)."""
    paths = dict(item.split("=", 1) for item in spec.split(",") if "=" in item)
    return {name: shutil.disk_usage(p).free for name, p in paths.items() if os.path.isdir(p)}


def load_env(env_file):
    """WATCHER_* settings from an optional KEY=VALUE file; real env vars win."""
    env = {}
    if env_file:
        for line in Path(env_file).read_text().splitlines():
            k, sep, v = line.strip().partition("=")
            if sep and not k.startswith("#"):
                env[k.strip().removeprefix("export ").strip()] = v.strip().strip("'\"")
    env.update({k: v for k, v in os.environ.items() if k.startswith("WATCHER_")})
    return env


def post(url, title, body, secret, now):
    payload = {"kind": "push", "source": "offline-library", "title": title, "body": body,
               "severity": "info", "key": f"offline-library-{now:%Y-%m}", "entity": "", "url": ""}
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "User-Agent": UA,
                                          "X-Bot-Secret": secret})
    with urllib.request.urlopen(req, timeout=30) as r:
        r.read()


def save_state(path, state):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(state, indent=1, sort_keys=True))
    os.replace(tmp, path)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="print the digest; don't post or save state")
    ap.add_argument("--state", help=f"state file (default WATCHER_STATE or ./{DEFAULT_STATE})")
    ap.add_argument("--env-file", help="KEY=VALUE file with the WATCHER_* settings")
    args = ap.parse_args(argv)
    env = load_env(args.env_file)

    cfg = json.loads((HERE / "sources.json").read_text())
    state_path = Path(args.state or env.get("WATCHER_STATE") or DEFAULT_STATE)
    old_state = json.loads(state_path.read_text()) if state_path.exists() else {}
    now = dt.datetime.now(dt.timezone.utc)
    title, body, new_state = run(cfg, old_state, http_get, free_space(env.get("WATCHER_FREE_PATHS", "")), now)

    if args.dry_run:
        print(f"{title}\n\n{body}")
        return 0
    url, secret = env.get("WATCHER_ALERT_URL", ""), env.get("WATCHER_ALERT_SECRET", "")
    if not (url and secret):
        print("WATCHER_ALERT_URL and WATCHER_ALERT_SECRET must be set (env or --env-file); state not saved",
              file=sys.stderr)
        return 2
    try:
        post(url, title, body, secret, now)
    except Exception as e:
        print(f"posting to the webhook failed: {err(e)}; state not saved", file=sys.stderr)
        return 1
    save_state(state_path, new_state)
    print(title)
    return 0


if __name__ == "__main__":
    sys.exit(main())
