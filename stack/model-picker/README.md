# Chat model picker

The optional Compose overlay adds independent **Host** and **Family** filters to
the chat picker. Both work with search and the existing connection and tag
filter. For example, choose PC and Gemma to narrow the list to that combination.

For this project's two-host layout, an unprefixed Ollama model defaults to Mac
and a `pc.` prefix identifies the PC. To override either label, add a connection
tag such as `Host:Studio` under Admin → Settings → Connections. A plain Mac or PC
tag also works. Terminal agents appear under Terminal when a terminal is selected.
Family labels are inferred from model IDs, base IDs and names. An unknown family
stays in All families.

Active, visible models saved in Workspace stay at the bottom as disabled rows
if discovery loses them. This also works on a fresh page while a host is down.
For a model that exists only through auto-discovery, **pin it while it is
visible** to keep a disabled row if it disappears. The next catalog refresh restores the live entry when the
model returns. A fresh page can recover the ID from personal pins. Display names
and host labels learned during discovery last for the lifetime of the picker.
An unpinned auto-discovered model disappears when its host goes away. Accessible
workspace presets also show as unavailable when their base model is missing
and server-side fallback is disabled.

An unloaded Ollama model can still accept a chat. A terminal agent's status
follows discovery for the selected terminal. A CLI can list models before its
provider rejects a request, so this indicator cannot verify subscription login.

## Build and run

From the stack directory, with the usual stack environment configured:

```sh
docker compose -f compose.yaml -f model-picker.compose.yaml build chat
docker compose -f compose.yaml -f model-picker.compose.yaml up -d --no-deps chat
```

The first build needs internet access. It applies a small source patch to the
pinned Open WebUI revision, then copies the compiled interface and model-list
handler into the matching runtime image. The base stack supplies the same chat
data, branding and configuration. For an offline server, build for the server's
architecture and transfer the image with Docker save/load before running Compose.

To roll back, run `docker compose -f compose.yaml up -d --no-deps chat`.
Recheck the patch and runtime image together before upgrading Open WebUI.
Run the filter tests with `node --test model-picker/picker.test.mjs` from the
stack directory.
