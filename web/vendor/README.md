# Vendored files

Served as-is so the web pages work with no internet access. Do not edit; replace
the whole folder when upgrading and update this list.

| Folder | Version | Source | License |
|---|---|---|---|
| `maplibre-gl-6.16.0/` | maplibre-gl 6.16.0 (`dist/maplibre-gl.mjs`, `dist/maplibre-gl-worker.mjs`, `dist/maplibre-gl.css`) | https://registry.npmjs.org/maplibre-gl/-/maplibre-gl-6.16.0.tgz | BSD-3-Clause (`LICENSE.txt`) |
| `pmtiles-4.5.0/` | pmtiles 4.5.0 (`dist/pmtiles.js`, IIFE global `pmtiles`) | https://registry.npmjs.org/pmtiles/-/pmtiles-4.5.0.tgz | BSD-3-Clause (https://github.com/protomaps/PMTiles/blob/main/LICENSE) |
| `protomaps-basemaps-5.7.2/` | @protomaps/basemaps 5.7.2 (`dist/basemaps.js`, IIFE global `basemaps`) | https://registry.npmjs.org/@protomaps/basemaps/-/basemaps-5.7.2.tgz | BSD-3-Clause (https://github.com/protomaps/basemaps/blob/main/LICENSE) |
| `basemaps-assets/fonts/Noto Sans Regular/` | all 256 glyph ranges | https://github.com/protomaps/basemaps-assets at commit `028c18f713baecad011301ff7a69acc39bcc2ae7` (`fonts/Noto Sans Regular/`) | SIL OFL 1.1 (`basemaps-assets/fonts/OFL.txt`) |
| `basemaps-assets/sprites/v4/` | `light`, `dark` (1x and 2x) | same repo and commit (`sprites/v4/`) | see https://github.com/protomaps/basemaps-assets |

The map style comes from `basemaps.layers()` at runtime; every `text-font` is
rewritten to the single vendored stack, `Noto Sans Regular`. Map tiles
(`/tiles/planet.pmtiles`) are not vendored: on the server they live in
`$LIBRARY_DIR/maps/`; locally `web/tiles/` holds a small git-ignored
test extract.
