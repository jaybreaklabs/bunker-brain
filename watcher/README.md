# Release watcher

Monthly, notify-only. `watch.py` checks the sources in `sources.json`, compares
them with the last run's state, and posts one digest as JSON to a webhook
(`POST $WATCHER_ALERT_URL`, header `X-Bot-Secret`, fields `kind` `push`,
`source`, `title`, `body`, `severity`, `key` `offline-library-YYYY-MM`). Python 3.11 stdlib only. Design: `SPEC.md` §8.

| Source | What is compared |
|---|---|
| Kiwix OPDS | newest `updated` per name + flavour, size from the acquisition link `length`. Tracks every entry in `content/zims.json`; falls back to `default_zims` in `sources.json` if that file is missing |
| Protomaps | latest build `key` and `size` |
| OsmAnd | One line per map set in `groups` (regex on file name, e.g. all US maps, all world maps): newest `timestamp` and total `containerSize` |
| GitHub releases | `tag_name` of the latest release (Organic Maps, llama.cpp, Ollama, Open WebUI, kiwix-tools) |
| Hugging Face | repos created since the last run, per org, after the optional `include` / `exclude` regexes (an org's own regex overrides the source-wide `exclude`) |

The first run (empty or missing state) only records a baseline and says so. A
source added later gets its own baseline the first time it is seen. A source
that fails is listed under "Problems" and keeps its previous state, so the next
run compares against the last good value. The state is saved only after the
digest is posted; a failed post exits non-zero and the next run reports again.

## Settings

All `WATCHER_*` settings come from the environment or an `--env-file`
(`KEY=VALUE` lines; real env vars win). Keep the file outside the repo, mode `600`.

| Variable | Meaning |
|---|---|
| `WATCHER_ALERT_URL` | Webhook that receives the digest. Required for a real run |
| `WATCHER_ALERT_SECRET` | Sent as `X-Bot-Secret`. Required for a real run |
| `WATCHER_STATE` | State file (default `./watcher-state.json`; `--state` overrides). Delete it to start a fresh baseline |
| `WATCHER_FREE_PATHS` | Optional `name=/path,name=/path`; free space for each is added to the digest |

```sh
# watcher.env (example)
WATCHER_ALERT_URL=http://192.0.2.20:8770/alert
WATCHER_ALERT_SECRET=change-me
WATCHER_STATE=/srv/bunker-brain/config/watcher-state.json
WATCHER_FREE_PATHS=library=/srv/bunker-brain/library,models=/srv/bunker-brain/models
```

## Running it monthly

Any scheduler works. Example cron line (09:00 on the 1st):

```
0 9 1 * * python3 /srv/bunker-brain/repo/watcher/watch.py --env-file /srv/bunker-brain/config/watcher.env
```

On TrueNAS SCALE: System → Advanced Settings → Cron Jobs, same command; leave
"Hide Standard Error" unchecked so failures reach the alert mail. Only
`watcher/` and `content/zims.json` need to be on the host.

## Usage

```sh
python3 watch.py --dry-run                      # print the digest; no post, state untouched
python3 watch.py --dry-run --state /tmp/s.json  # try against a scratch state file
python3 watch.py --env-file /path/watcher.env   # real run: post, then save state
```

## Tests

```sh
cd watcher && python3 -m unittest test_watch
```

The tests use trimmed real responses in `fixtures/` (captured 2026-11-17) and
make no network calls.
