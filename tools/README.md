# Offline library search tool (Open WebUI)

`kiwix_search.py` is an Open WebUI Tool. It lets a chat model search the Kiwix
library through kiwix-serve and cite pages with links to your public library URL.

- `search_library(query)`: full-text search across all books
  (`GET /search?pattern=…&format=xml&pageLength=N`, optional
  `books.filter.name=<name>` per restricted book), then fetches the top articles,
  strips them to text, trims each to the char budget, and returns numbered
  sources `[n]` with public URLs. Emits one `citation` event per source.
- `list_books()`: book names and titles from `/catalog/v2/entries`.

Stdlib only, plus `pydantic` (already part of Open WebUI).

## Install

1. Open WebUI → **Workspace → Tools → +** (New Tool).
2. Paste the contents of `kiwix_search.py`, keep the id `kiwix_search`, **Save**.
   (Or use **Import** on the Tools page with this file.)

## Settings (valves)

Workspace → Tools → gear icon on *Offline Library Search*:

| Valve | Default | Notes |
|---|---|---|
| `KIWIX_BASE_URL` | `http://kiwix:8080` | URL the Open WebUI container uses (service name on a shared Docker network, or host IP and port). If kiwix-serve runs with `--urlRootLocation /library`, append `/library`. |
| `PUBLIC_BASE_URL` | `https://wiki.example.com/library` | Prefix for links in citations. Must point at the same URL root users browse. |
| `MAX_RESULTS` | 5 | Articles fetched per search. |
| `MAX_CHARS_PER_ARTICLE` | 3000 | Text budget per article. Lower it for small-context models. |
| `BOOKS` | empty | Comma list of book names from `list_books()` (e.g. `wikivoyage_en_all`) to restrict search. Empty = all books. |

## Enable for a model

- Per model: **Workspace → Models → edit the model → Tools → tick
  Offline Library Search → Save**. Set **Advanced Params → Function Calling =
  Native** if the model supports tool calls.
- Per chat: the **+** / tools toggle under the message box.

## Notes

- Books without a full-text index (catalog tag `_ftindex:no`, e.g. the Water
  Treatment Library) return no search hits; only indexed books are searched.
- Medical and survival answers: the tool tells the model to treat the library as
  the source and itself as a guide, not an authority. Keep that wording.

## Tests

```sh
cd tools
python3 -m unittest -v test_kiwix_search            # fixtures only
KIWIX_LIVE=1 python3 -m unittest -v test_kiwix_search   # also hits the live server
```

Fixtures in `fixtures/` are real responses captured from kiwix-serve 3.8.2.
