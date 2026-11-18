# AGENTS.md — bunker-brain

Guidance for any coding agent working in this repo. Read this first, then
`SPEC.md`, the source of truth for what is being built and why.

If `local/AGENTS.local.md` exists, read it too: it holds the operator's own
deployment details and house rules. It is git-ignored and never committed.

## What this project is

A self-hosted offline library that keeps working when the internet doesn't:

- **Library**: Kiwix ZIM files (Wikipedia, sister projects, survival / repair /
  medical collections) served by `kiwix-serve`.
- **Map**: Protomaps planet PMTiles with a MapLibre page that shows live GPS.
- **Chat**: Open WebUI calling local LLMs, with a tool that searches the library
  and cites pages.
- **Model archive**: curated open-weight models, their runtimes, and a
  `BRIEF.md` per model, stored for offline use.
- **Release watcher**: a monthly script that reports new library, map, model and
  runtime releases to a webhook.

The repo holds code, config, manifests and docs only. Content and model weights
are never committed or redistributed.

## Hard rules

1. **Nothing personal in the repo, ever.** Write everything as if the repo goes
   public tomorrow, and keep that true in the history too. No real names,
   emails, usernames, domains, hostnames, IP addresses, network layout, home
   hardware inventory, locations, family details, account names or secrets in
   code, config, tests, fixtures, docs or commit messages.
   - Use placeholders: `example.com` / `wiki.example.com` for domains,
     `192.0.2.x` (RFC 5737) for IPs, `/srv/bunker-brain/...` for paths.
   - Real values go in git-ignored files: `local/` (notes, change records,
     deployment details), `stack/.env`, `web/links.json`, `*.env`. Commit a
     `*.example` file next to anything that needs one.
   - Before every commit, grep the staged diff for addresses, domains and names.
     If something personal was ever committed, rewrite history, don't just
     delete it in a new commit.
   - Commits use the GitHub noreply email, not a personal one.
2. **No secrets in the repo.** Tokens live in git-ignored env files. Don't print
   them in logs or chat.
3. **No Docker socket mounts** in this project's containers.
4. **Verify downloads by hash** before moving them into place. Never replace a
   working file until the new one is verified. Large Kiwix files: use the aria2
   torrent stacks in `stack/`, not plain HTTP (mirrors throttle to ~1–2 MB/s).
5. **Pin sources.** Model downloads name an exact Hugging Face `owner/repo`;
   no search-based resolution. Container images by tag or digest.
6. **Medical and survival output is guidance to sources, not authority.** Keep
   the disclaimer in the chat tool, the landing page and briefs.

## Configuration

| What | Where | Example file |
|---|---|---|
| Host paths for the compose stacks | `stack/.env` | `stack/.env.example` |
| "Around the house" links and the chat URL on the landing page | `web/links.json` | `web/links.example.json` |
| Watcher webhook URL, secret, state path, free-space paths | env vars or `--env-file` | `watcher/README.md` |
| Chat tool URLs | Open WebUI valves | `tools/README.md` |

## Repo layout

```
SPEC.md              design and decisions
AGENTS.md            this file (CLAUDE.md imports it)
WHATS-IN-IT.md       shareable list of the content and models
content/zims.json    library manifest (+ check/test scripts)
content/knowledge/   curated safety quick reference (official sources, dated) for the chat's knowledge base
fetch/               builds aria2 input lists for the bulk download
stack/               compose stacks: kiwix, one-shot fetch, bulk fetch
web/                 landing page, collections, map page, vendored JS/fonts
web/brand/           design system: tokens, components, logo and icons (see its README)
stack/chat-brand/    Open WebUI name, logo and theme, from the same tokens
tools/               Open WebUI library-search tool + tests
watcher/             release watcher (stdlib Python) + tests
local/               git-ignored: the operator's own deployment notes
```

## Conventions

- **Python**: stdlib only unless there's a strong reason; `unittest`, not
  pytest. One small test per non-trivial piece of logic.
- **Web**: plain HTML/CSS/JS, no build step. Must work on a phone and fully
  offline: no CDN links, fonts or scripts from the internet.
- **Look**: build pages from `web/brand/` (tokens, components, `ui.js`); keep
  page-only CSS to layout. Colours live in `tokens.css` only.
- **Keep it small.** Prefer an existing tool's feature over new code.

## Model briefs

Every model folder gets a `BRIEF.md`, written after the model is downloaded and
tested, never from research alone:

```markdown
# <Model name> — <quant>
**Use for:** … **Avoid for:** …
**Runs on:** memory needed at 8k / 32k context; machines it was tested on. Speed: <tok/s measured>.
**Runtime:** llama.cpp <tag> (path in runtimes/) | Ollama <version> | MLX
**Files:** <gguf>, <mmproj?>
**Run:** `…`
**Settings:** temperature …, context …, template …, --n-cpu-moe …
**Open WebUI connection:** …
**License:** … **Source:** <repo>@<revision>, downloaded <date>, sha256 in SHA256SUMS
```

Regenerate `INDEX.md` whenever a brief changes.

## Before you finish a task

- Run the relevant tests.
- Check the diff for anything personal (rule 1).
- Say what's done, what's untested, and anything you couldn't check.
