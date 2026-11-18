# Chat branding (Open WebUI)

Files mounted read-only into the chat container by `stack/compose.yaml`.

At start-up Open WebUI clears its served static folder and copies
`/app/build/static/` into it, so mounting over files in `/app/build/static/`
replaces them (checked against the v0.13.3 source: `backend/open_webui/config.py`,
`src/app.html`). `WEBUI_NAME` sets the name; Open WebUI shows it as
"Bunker Brain (Open WebUI)".

| File | Shown as |
|---|---|
| `custom.css` | Theme: re-points Open WebUI's grey scale to the brand's paper-to-olive ramp, serif headings in answers, ochre links. |
| `favicon.png`, `logo.png`, `web-app-manifest-*.png` | App icon (sidebar, install icon). |
| `favicon.svg`, `favicon.ico`, `favicon-96x96.png` | Browser tab. |
| `apple-touch-icon.png` | iOS home screen. |
| `splash.png`, `splash-dark.png` | Loading screen, light and dark. |

The palette block in `custom.css` must match `web/brand/tokens.css`
(`web/test_brand.py` checks it).

**License:** Open WebUI's license allows replacing its branding only for
deployments with 50 or fewer users in any 30 days (or with an enterprise
license). A home server fits; a bigger deployment should drop these mounts.

**Upgrading Open WebUI:** if a new version moves `build/static` or renames these
files, the mounts stop doing anything (nothing breaks, the stock look returns).
Re-check the paths above against the new version's source.
