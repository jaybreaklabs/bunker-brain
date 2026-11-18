# Bunker Brain design system

The "Contour Atlas" identity: olive, sand and ochre, a contour-line brain mark,
serif headings over a plain sans body. Everything here works offline: system
fonts only, no CDN, no web fonts.

## Files

| File | What it is |
|---|---|
| `tokens.css` | Every colour, font, size and spacing value. Palette first, then *roles* (`--bb-bg`, `--bb-text`, `--bb-rule`…). Dark mode only re-points roles. |
| `components.css` | The components below. They read role tokens only. |
| `ui.js` | ES module with one function per component, returning DOM nodes. |
| `lockup-cream.png` | Logo + wordmark for the dark header bar. |
| `favicon.svg`, `favicon.ico`, `favicon-32.png` | Browser tab icon (simplified brain for small sizes). |
| `app-icon-180/192/512.png` | Home-screen icons (`/manifest.webmanifest`, apple-touch-icon). |
| `terrain.jpg` | Illustrated terrain used on the map card. Not real map data. |

Pages load the two stylesheets and import from `ui.js`:

```html
<link rel="stylesheet" href="/brand/tokens.css">
<link rel="stylesheet" href="/brand/components.css">
<script type="module">
  import { row, index, searchForm } from "/brand/ui.js";
</script>
```

## Components

| Function (`ui.js`) | Class | Use |
|---|---|---|
| (static markup) | `.bb-header`, `.bb-nav`, `.bb-main`, `.bb-footer` | Page frame: olive bar with logo and nav, content column, disclaimer footer. |
| `searchForm()` | `.bb-search` | Full-text search across all books (kiwix-serve). |
| `row({href, title, sub, iconName, thumb, variant, end})` | `.bb-row`, `--inline`, `--tall` | One line of a ruled list: icon or thumbnail, title, subtitle, arrow or count. |
| `index(rows)` | `.bb-index` | Ruled list that holds rows. |
| `card({href, image, title, sub})` | `.bb-card` | Picture with a dark caption (the map preview). |
| `button({href, label, iconName, variant})` | `.bb-button`, `--soft`, `--paper` | Solid, sand or floating paper button. |
| `strip(links)` | `.bb-strip` | Wrapping line of small icon links. |
| `crumb(parts)` | `.bb-crumb` | Breadcrumb, monospace. |
| `linkList(links)` | `.bb-links` | "Around the house" links with a "No DNS?" fallback. |
| `status(text)`, `alert(text)` | `.bb-status`, `.bb-alert` | Quiet message, red banner. |
| `icon(name)` | `.bb-icon` | Line icons in `ICONS`; stroke follows the text colour. |

Type helpers: `.bb-display` (page title), `.bb-heading`, `.bb-subheading`, `.bb-lead`, `.bb-narrow`.

## Changing things

- **A colour:** edit the palette or the role in `tokens.css`. If you change one of
  the five palette colours, change it in `stack/chat-brand/custom.css` too;
  `web/test_brand.py` fails until they match.
- **A subject's name, icon, order or blurb:** `SUBJECTS` in `web/library.js`.
- **A new page:** load the two stylesheets, use `.bb-header`/`.bb-main`/`.bb-footer`,
  build content with `ui.js`. Keep page-only CSS to layout.

## Palette

| Token | Hex | Use |
|---|---|---|
| `--bb-bunker-olive` | `#293420` | Mark, headings, header bar |
| `--bb-field-olive` | `#495435` | Secondary ink and rules |
| `--bb-ochre` | `#C5A646` | Selected actions, citations, dark-mode buttons |
| `--bb-sand` | `#E7DFC9` | Secondary panels, footer |
| `--bb-paper` | `#F7F2E5` | Reading surface, reverse mark |

## Source

Artwork from the Bunker Brain design kit (Contour Atlas identity), made for this
project. The PNGs were resized and re-saved without metadata. The kit's terrain
picture is illustrative, not map data.
