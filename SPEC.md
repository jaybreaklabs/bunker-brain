# Offline Library — Design Spec

Status: draft, 2026-11-17. Project name: `bunker-brain` (internal paths and
stack names still say `offline-library`). Examples use `wiki.example.com`.

## 1. Goal

A private, self-hosted "everything you need offline" library for the household:
Wikipedia and sister projects, practical survival / repair / medical content, a
world map with live location, an AI chat that answers from the library with
citations, and an archive of the best open-weight AI models in case frontier
APIs become unavailable.

It must keep working at home with the internet down, as long as there is power.

### Non-goals (for now)

- Public hosting. LAN + WireGuard only.
- Server-side turn-by-turn routing or address geocoding (phones do this; see §6).
- Live-updated Wikipedia (daily edits). Kiwix builds are the update unit.
- Redistributing any content or model weights. If the project is open-sourced
  later, only code, config and download manifests are published.

## 2. Prior art and what we take from it

| Project | Use | Why |
|---|---|---|
| Project N.O.M.A.D. (Crosstalk-Solutions, Apache-2.0) | Crib ideas and code, don't run it | Its admin app manages containers through the Docker socket (root-equivalent, fights TrueNAS/Dockge) and has no auth. We copy its component choices: Kiwix, PMTiles/MapLibre, an LLM chat with RAG. Keep its NOTICE/attribution for anything copied. |
| Lastbook (Immortal-Protocols, MIT) | Ideas only | Packs are not public, server isn't containerized. Borrow: curated topic guides that point into the library, answers that cite pages. |
| Internet-in-a-Box | Reference | Ansible / whole-machine install; too heavy. |

## 3. Architecture

```
 phone / laptop (LAN or VPN)
        │  DNS: local resolver with split-horizon records
        │  HTTPS
        ▼
 NAS: reverse proxy (wildcard cert) + compose stack
   ├─ landing page (static)      wiki.example.com/
   ├─ kiwix-serve                wiki.example.com/library/
   ├─ map page + PMTiles         wiki.example.com/map/
   ├─ Open WebUI                 chat.example.com   (no sub-path support)
   └─ release watcher (cron job, §8)
        │  OpenAI-compatible API, on demand
        ▼
 LLM hosts: Apple-silicon Mac (Ollama / llama-server) and/or
            a GPU PC (llama-server, woken on demand)
```

### 3.1 Containers (one compose stack in Dockge)

| Service | Image | Notes |
|---|---|---|
| kiwix | `ghcr.io/kiwix/kiwix-serve:3.8.2` | `--urlRootLocation=/library *.zim`. Restart after adding ZIMs (a `library.xml` + `--monitorLibrary` would avoid that; not needed yet). |
| web | `caddy:2.11.6-alpine` (`stack/Caddyfile`) | Proxies `/library` to kiwix. Landing page, `/map/` (MapLibre + `pmtiles` JS, `GeolocateControl`), serves `.pmtiles` with range requests. |
| chat | `ghcr.io/open-webui/open-webui:v0.13.3` (pinned: upgrades can migrate the DB) | Own name (`chat.example.com`); Open WebUI doesn't support a sub-path. Connections to the LLM hosts' endpoints. Has its own login, unlike N.O.M.A.D. |

No Docker socket mounts. Nothing here manages other containers.

### 3.2 Network and access

- Local DNS (e.g. Pi-hole) answers `wiki.example.com` and `chat.example.com`
  with the NAS's LAN address. With Pi-hole, also add `local=/<name>/` dnsmasq
  lines so HTTPS/AAAA queries don't leak upstream and return NXDOMAIN.
- A reverse proxy on the NAS terminates HTTPS with a wildcard cert, so phone
  browsers allow geolocation (it needs a secure context).
- Internet down: everything still works on home Wi-Fi. Certs are cached
  (~90-day lifetime).
- DNS host down: use fallback bookmarks to `http://<nas-ip>:<port>`. No HTTPS,
  so no live location on the map in that mode.
- Power is the real single point of failure → UPS for NAS, router, switch and
  DNS host (out of scope here).

## 4. Storage (NAS)

Use a large HDD pool; avoid small or nearly full SSD pools. Three datasets
(paths go in `stack/.env`, see `stack/.env.example`):

| Dataset | Holds | Quota | Settings |
|---|---|---|---|
| library (`LIBRARY_DIR`) | ZIMs, PMTiles, phone map files, landing page | 950 G | `recordsize=1M`, `compression=lz4` |
| models (`MODELS_DIR`) | Model archive + runtimes | 1.05 T | `recordsize=1M`, `compression=lz4` |
| config (`CONFIG_DIR`) | Open WebUI data, kiwix `library.xml`, fetch lists, watcher state | 20 G | defaults |

Backups: the library is re-downloadable, so no backup beyond ZFS mirroring.
Models can disappear upstream, so the models dataset gets snapshots and
should get an off-NAS copy eventually (open question §11).

Total budget: 2 TB. Keep ~240 G free inside the quotas for update swaps
(new file lands beside the old one until verified).

## 5. Library content

All Kiwix ZIMs unless noted. Sizes from the Kiwix catalog, Nov 2026.

| # | Collection | Size | Running |
|---|---|---|---|
| 1 | Wikipedia EN maxi (2026-08) | 127 G | 127 |
| 2 | Wiktionary, Wikibooks, Wikisource, Wikiversity, Wikivoyage | ~30 G | 157 |
| 3 | Survival starter: iFixit, Appropedia, DIY StackExchange, WikiMed, MDWiki, Military Medicine, zimgit-medicine, Ready.gov, Army field manuals, CD3WD, Low-tech Magazine, True Prepper | ~27 G | 184 |
| 4 | StackExchange set: electronics, math, physics, chemistry, biology, gardening, cooking, outdoors, ham, mechanics, woodworking, engineering, earth science, medical sciences, sustainability | ~16 G | 200 |
| 5 | Post-Disaster Library (zimgit set), Simple English Wikipedia, ArchWiki | ~5 G | 205 |
| 6 | LibreTexts (all 13 subjects) | ~18 G | 223 |
| 7 | Gutenberg subsets: science, technology, agriculture, medicine, military, social, geography, library science | ~52 G | 275 |
| 8 | Crash Course (video) | 21 G | 296 |
| 9 | Survivor Library (zimit crawl, ~13.7k pre-1930 scanned books) | 220 G | ~516 |

Skipped: Khan Academy (180 G, 2023 build), full Gutenberg (206 G; subsets cover
the useful part), wikiHow (no longer published).

Survivor Library: downloaded and SHA-256 verified 2026-11-17. **Test result:**
Kiwix full-text search covers only the ~175 crawled category pages, not the
text inside the PDFs ("beekeeping" → 3 category pages; "blacksmithing" → 0).
Title search (the search box's suggestions) does find books by file name
(e.g. `blacksmith_shop_practice_1910.pdf`), and the PDFs open in the browser.
The sampled PDF has a text layer, so a later enhancement can extract PDF text
(`pdftotext`) into our own search index for the chat tool. Kept for now:
it's within budget and the content is unique.

### 5.1 Organization

- The landing page groups collections into sections: Medical, Water & Food,
  Repair & Build, Power & Energy, Reference, Learning, Maps, Ask.
- Section membership lives in one `collections.json` in the repo
  (ZIM name → section, display name, one-line description).
- Kiwix's own catalog search and cross-book full-text search stay available
  under `/library/`.
- Later: Lastbook-style topic guides ("purify water", "treat a burn") that link
  straight to the relevant pages. Not in v1.

### 5.2 Licensing

Wikimedia content is CC BY-SA. Government manuals are mostly public domain.
iFixit is CC BY-NC-SA. True Prepper and Survivor Library terms are unclear.
Fine for private use. Never redistribute content.

## 6. Maps

| Where | What | Size |
|---|---|---|
| NAS web map | Protomaps planet PMTiles (z0–15), latest build | ~140 G |
| NAS phone-map backup | OsmAnd world vector maps + US contour lines + US Wikipedia POIs | ~137 G |
| Phones (large storage) | Same OsmAnd set downloaded in-app; Organic Maps as a second app | ~137 G per phone |

- Web map: browse anywhere in the world, live GPS dot via the browser
  Geolocation API (works offline over HTTPS). Search by place name is a v2 item.
- Navigation: turn-by-turn and address search happen on the phone (OsmAnd /
  Organic Maps), which also works away from home where the NAS isn't reachable.
- OsmAnd monthly map updates need its paid tier. Organic Maps updates are free.
- Unverified: whether OsmAnd `.obf` files copied in through the iOS Files app
  are picked up. Test one file before relying on the NAS backup for phones.

## 7. AI

### 7.1 Chat

- Open WebUI on the NAS at `chat.example.com`, linked from the landing page
  (`web/links.json`, entry `"id": "chat"`). Costs nothing when idle.
- Backends, configured as OpenAI-compatible connections:
  - Mac: Ollama, bound to the LAN (`OLLAMA_HOST=0.0.0.0`) with a firewall
    rule limiting access to the NAS.
  - PC: `llama-server --host 0.0.0.0` started on demand; wake-on-LAN sent from a
    host on the PC's subnet.
- If no backend is awake, the chat page loads and reports the model as
  unavailable. Everything else keeps working.

### 7.2 Library search tool (the part worth open-sourcing)

No giant vector index over 500 G of content. Instead an Open WebUI tool that:

1. Calls kiwix-serve full-text search (`/library/search?pattern=…`) across books.
2. Fetches the top articles, strips HTML to text, trims to a budget.
3. Returns snippets with their public `/library/...` URLs so the model
   cites pages and the user can click through.

Optional later: a small embedding index (Qwen3-Embedding) over the curated
survival collections only, for meaning-based search.

Medical and survival answers carry a fixed disclaimer: the model points to
sources; it is not the authority.

### 7.3 Model archive

Layout in the models dataset:

```
models/<family>/<model>/
  <model>-<quant>.gguf            (shards if split)
  mmproj-*.gguf                   (vision projector, if any)
  BRIEF.md                        (our own write-up, see below)
  README.md   LICENSE   chat_template.jinja   tokenizer*
  SHA256SUMS                      (checked against HF LFS sha256)
  manifest.json                   (repo, revision, date, params, quant, size, license, runs-on)
INDEX.md                          (one table of every model: use case, size, machine, link to its BRIEF)
runtimes/
  llama.cpp/<tag>/  source tarball + macOS and Windows builds
  llama.cpp-unsloth/<branch>/     (fork needed for DeepSeek V4.1 Flash today)
  ollama/<version>/   lmstudio/<version>/   (installers)
  images/   open-webui.tar  kiwix-serve.tar  comfyui.tar  (docker save)
```

Each `BRIEF.md` is written so someone could use the model with no internet and
no prior context:

- **What it's for**: intended use cases, and what it's bad at.
- **Where it runs**: which machine(s), memory needed at 8k / 32k context,
  expected speed once measured.
- **Tech stack**: the runtime and the exact version in `runtimes/` known to work
  (e.g. mainline llama.cpp `bNNNN`, or the unsloth fork for DeepSeek), plus any
  extra files (mmproj, draft model).
- **How to run it**: copy-paste commands for the Mac and the PC
  (`llama-server …`, `ollama create …`), and recommended settings
  (temperature, context size, chat template, `--n-cpu-moe` value).
- **How to connect it**: the Open WebUI connection settings.
- **License** in one line, and the source repo + revision.

Briefs are written when a model is downloaded and tested in Phase 0/4, not from
the research alone; speeds and memory figures are filled in from real runs.

Format rule: GGUF is the archive format (every runtime reads it). MLX copies
only for the one or two models used daily on the Mac. Don't re-quantize
vendor-native FP4/QAT checkpoints — use them as shipped.

Using a model on a machine: `rsync -aP` the folder to local SSD once
(~3 min per 20 G at 1 GbE), then load it locally. Don't run models straight off
the SMB share. Import into Ollama with a `Modelfile` (`FROM ./model.gguf`).

Tiers are by memory class. "Mac" means a 64 GB Apple-silicon machine; "PC"
means a 16 GB GPU with 32 GB of system RAM (MoE experts offloaded to RAM).

#### Tier A — runs on 64 GB-class hardware (~150 G)

| Model | Quant | Size | Runs on | License |
|---|---|---|---|---|
| Qwen3.8-27B | UD-Q6_K_XL | 25 G | Mac | Apache-2.0 |
| Gemma 4 31B-it | UD-Q6_K_XL | 28 G | Mac | Apache-2.0 |
| Qwen3.6-35B-A3B | UD-Q6_K | 29 G | Mac; PC with expert offload | Apache-2.0 |
| Gemma 4 26B-A4B-it | Q4_K_M | ~17 G | PC; Mac | Apache-2.0 |
| Nemotron 3.5 Bolt 74B-A9B | UD-Q4_K_XL | 50 G | Mac (after raising `iogpu.wired_limit_mb`) | OpenMDW-1.1 |

#### Tier B — needs ~128 G of memory (~198 G)

| Model | Quant | Size | License |
|---|---|---|---|
| Nemotron 3.5 Super VL 120B-A12B | UD-Q4_K_XL | 87 G | OpenMDW-1.1 |
| Qwen3.8-Flash-Next 125B-A6B | UD-Q4_K_XL | 111 G | qwen-community-1.0 (restrictive) |

#### Tier C — archive only (~501 G)

| Model | Quant | Size | License |
|---|---|---|---|
| DeepSeek V4.1 Flash 1017 (~750B MoE) | UD-Q4_K_XL | 501 G | MIT |

**Decision: DeepSeek is downloaded.** It's the strongest open model available
and the main reason the budget went to 2 TB. No consumer machine can run it
today (it needs roughly 512 G+ of memory at this quant), so it's pure insurance
for future hardware. It's downloaded last, after the runnable tiers, together
with the llama.cpp fork that currently supports it. If space gets tight, the
fallback is its UD-IQ3_S quant (424 G), not dropping it.

Considered and left out: GLM-5.3 (282 G, weaker than DeepSeek, custom license),
Mistral Large 4 (424 G, weak scores), Kimi K3.1 Pro (#1 but ~1.56 T native, no
GGUF yet — watcher flags it), Qwen3.8-2.4T, Meta Muse Spark Open.

#### Specialists (~110 G)

| Need | Pick | Backup |
|---|---|---|
| OCR / documents | GLM-OCR 0.9B | Unlimited-OCR-2 |
| Vision, small | Gemma 4 12B QAT (7 G) | — |
| Phone | Gemma 4 E4B QAT (5 G) | Gemma 4 E2B |
| Medical | MedGemma 1.5 4B | MedGemma 27B (Q4, 16 G) |
| Embeddings | Qwen3-Embedding-8B + 0.6B | harrier-oss-v1-0.6b |
| Reranker | Qwen3-Reranker-4B | — |
| Speech-to-text | Nemotron 3.5 Transcribe 30B-A4B | Whisper large-v3-turbo, Parakeet TDT 0.6B v3 |
| Text-to-speech | Kokoro-82M | VoxCPM2 |
| Translation | TranslateGemma 12B | MADLAD-400 |
| Image generation | Z-Image-Turbo | FLUX.2 klein 4B |

Optional: BF16 original of Qwen3.8-27B (~56 G) for re-quantizing later.

Model total incl. runtimes: ~970 G.

### 7.4 Hardware notes

- Apple silicon: the default GPU memory cap is ~75% of RAM (~48 G of 64 G).
  Raise it with `sudo sysctl iogpu.wired_limit_mb=<MB>` (resets on reboot).
  Prompt processing is the slow part for long RAG contexts.
- GPU PC: MoE models run with experts in system RAM (`-ngl 99 --n-cpu-moe N`).
  16 G VRAM + 32 G RAM covers Tier A MoEs up to ~35 G; 96–128 G of RAM would
  cover Tier B.
- NAS: no GPU, never runs models.

## 8. Release watcher

One stdlib-only Python script, run monthly as a cron job on the NAS
(it needs the NAS's free-space numbers). Notify-only in v1.

Sources:

| Source | Endpoint | Compare |
|---|---|---|
| Kiwix | `opds.library.kiwix.org/catalog/v2/entries?name=<name>` | newest `updated` per name+flavour |
| Protomaps | `build-metadata.protomaps.dev/builds.json` | last `key` |
| OsmAnd | `download.osmand.net/get_indexes?gzip=true` | `timestamp` per tracked file |
| Organic Maps | GitHub releases `organicmaps/organicmaps` | `tag_name` |
| Hugging Face | `/api/models?author=<org>&sort=createdAt&direction=-1` for Qwen, google, deepseek-ai, nvidia, zai-org, mistralai, moonshotai, MiniMaxAI, unsloth, mlx-community | new repos since last run, filtered by name patterns; sizes from `?blobs=true` |
| Runtimes | GitHub releases for `ggml-org/llama.cpp`, `ollama/ollama`, `open-webui/open-webui`, `kiwix/kiwix-tools` | `tag_name` |

State in `state.json` (last-seen version per source). One digest per run,
posted to a webhook (e.g. a Discord bot):

- `POST $WATCHER_ALERT_URL`, header `X-Bot-Secret` (from a
  git-ignored env file), body
  `{"kind":"push","source":"offline-library","title":…,"body":…,"severity":"info","key":"offline-library-YYYY-MM"}`.
- Lines like: `Wikipedia maxi 2026-08 → 2026-11, +127 G, 410 G free`.

Download step (manual in v1): the `offline-library-fetch` Dockge stack
(`stack/fetch.compose.yaml`) runs aria2 on the item's `.torrent` into
`incoming/`. Then verify the published hash (meta4 / md5 / b3sum / sha256),
move it into place, remove the old file, and post a confirmation.

Why torrent: Kiwix HTTP mirrors throttle to ~1–2 MB/s per download (measured
2026-11-17; a 220 GB file would take 30+ hours), while a typical fiber line does
far more. The torrent (web seeds + peers) ran at ~100 MiB/s. Cap bulk torrents
(`stack/bulk.compose.yaml`): an uncapped ~1 Gbps run knocked a consumer
gateway offline. Usenet doesn't
carry these files, so it doesn't help. kiwix-serve picks up the
change via `--monitorLibrary`.

v2: approve-to-download buttons in the receiving bot.

Tests: one `unittest` file covering the version-diff logic against saved
sample responses.

## 9. Security

- Not exposed to the internet. Names resolve only through local DNS (LAN / VPN).
- Open WebUI uses its own accounts; signup disabled after creating ours.
- kiwix and the map are read-only and unauthenticated (LAN-only content).
- No Docker socket mounts. No secrets in the repo; bot secret in a git-ignored
  env file.
- Model and runtime downloads verified by hash before use.

## 10. Rollout

0. **Verify** (before big downloads)
   - Check PC system RAM.
   - Stand up kiwix-serve with two small ZIMs; confirm proxy, DNS and phone access.
   - Download Survivor Library sample or full ZIM; test full-text search.
   - Test OsmAnd sideload and PocketPal GGUF import on one phone.
   - Download Tier A models one at a time and confirm each loads in mainline
     llama.cpp / Ollama on the target machine.
1. **Library**: datasets, compose stack, landing page, ZIMs 1–8.
2. **Map**: planet PMTiles + map page with geolocation.
3. **Chat**: Open WebUI, Mac backend, library search tool.
4. **Model archive**: Tier A → specialists → runtimes → Tier B → Tier C,
   each with manifest, checksums and a tested BRIEF.md; INDEX.md kept current.
5. **Watcher**: script, cron job, first digest.
6. **Phones**: OsmAnd world + US contours, PocketPal with Gemma 4 E4B.
7. **Survivor Library** last, after the search test.

## 11. Open questions

- Off-NAS copy of the model archive (USB drive in a drawer? second site?).
- Mac firewall: restrict Ollama to the NAS IP (pf rule vs. app firewall).
- How the chat server reaches LLM hosts on another VLAN (allow rule vs. tunnel).
- PC RAM upgrade, and a UPS.

## 12. Caveats on the research

Model rankings came mostly from aggregator sites (ArtificialWatch, BenchLM),
not primary leaderboards; vendor benchmarks are self-reported. llama.cpp
support for the newest MoEs (Nemotron 3.5, Flash-Next, DeepSeek V4.1 Flash) is
unverified. Several sizes are estimates. Phase 0 exists to check all of this
before committing ~1 TB of downloads.
