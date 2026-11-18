// Bunker Brain UI components: small functions that return DOM nodes styled by
// /brand/components.css. Pages compose these instead of writing markup by hand.
// Plain ES module, no build step, works offline.

// Line icons from the Contour Atlas kit. Stroke follows the text colour.
const path = (d, w = 1.8) =>
  `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${d}" fill="none" stroke="currentColor" stroke-width="${w}" stroke-linecap="round" stroke-linejoin="round"/></svg>`;

export const ICONS = {
  preparedness: path("M2 20L12 3L22 20ZM8 20L12 12L16 20"),
  water: path("M12 2C10 6 5 10 5 15A7 7 0 0 0 19 15C19 10 14 5 12 2ZM8 15Q8 18 11 18"),
  repair: path("M15 3A6 6 0 0 0 8 11L2.8 17A2.5 2.5 0 0 0 7 21L13 14A6 6 0 0 0 21 7L17 11L13 7Z"),
  medical: path("M3 8H21V21H3ZM8 8V5H16V8M9 14H15M12 11V17"),
  power: path("M13 2L4 14H11L10 22L19 10H12Z"),
  book: path("M2 5Q8 3 12 7Q16 3 22 5V19Q16 17 12 21Q8 17 2 19ZM12 7V21"),
  learning: path("M2 9L12 4L22 9L12 14ZM6 11V16Q12 20 18 16V11"),
  box: path("M4 4H20V20H4ZM4 10H20"),
  ask: path("M3 3H21V16H10L5 21V16H3Z"),
  map: path("M2 6L8 3L16 6L22 3V18L16 21L8 18L2 21ZM8 3V18M16 6V21"),
  arrow: path("M5 12H19M13 6L19 12L13 18", 2),
  back: path("M19 12H5M11 6L5 12L11 18", 2),
  search: path("M10.5 3A7.5 7.5 0 1 0 10.5 18A7.5 7.5 0 1 0 10.5 3ZM16 16L21 21", 2),
  menu: path("M4 4H10V10H4ZM14 4H20V10H14ZM4 14H10V20H4ZM14 14H20V20H14Z", 1.6),
};

// el("a", { class: "x", href: "/" }, child, "text", null) -> <a>. null/false children are skipped.
export function el(tag, attrs = {}, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) if (v != null && v !== false) n.setAttribute(k, v);
  n.append(...kids.flat().filter((k) => k != null && k !== false));
  return n;
}

export function icon(name) {
  const s = el("span", { class: "bb-icon" });
  s.innerHTML = ICONS[name] || ICONS.box; // constant markup only
  return s;
}

const endArrow = () => el("span", { class: "bb-row__end", "aria-hidden": "true" }, icon("arrow"));

// A ruled list row. variant: "inline" (title and subtitle side by side on wide
// screens) or "tall" (bigger title). end: "arrow" (default), a count string, or null.
export function row({ href, title, sub, iconName, thumb, variant, end = "arrow", className } = {}) {
  const cls = ["bb-row", variant && `bb-row--${variant}`, className].filter(Boolean).join(" ");
  const a = el("a", { class: cls, href });
  if (iconName) a.append(icon(iconName));
  if (thumb) {
    const img = el("img", { class: "bb-row__thumb", src: thumb, alt: "", loading: "lazy", width: 36, height: 36 });
    img.onerror = () => img.remove();
    a.append(img);
  }
  a.append(el("span", { class: "bb-row__body" },
    el("strong", { class: "bb-row__title" }, title),
    sub ? el("span", { class: "bb-row__sub" }, sub) : null));
  if (end === "arrow") a.append(endArrow());
  else if (end != null) a.append(el("span", { class: "bb-row__count" }, end));
  return a;
}

export const index = (rows) => el("div", { class: "bb-index" }, rows);

// Full-text search across all books (kiwix-serve).
export function searchForm({ placeholder = "Search all books" } = {}) {
  const go = el("button", { type: "submit", "aria-label": "Search" }, icon("arrow"));
  return el("form", { class: "bb-search", action: "/library/search", method: "get", role: "search" },
    icon("search"),
    el("input", { type: "search", name: "pattern", placeholder, "aria-label": placeholder, required: "" }),
    // kiwix-serve refuses mixed-language searches; leave multilingual books (still browsable) out. Matches the chat tool's EXCLUDE_TAGS.
    el("input", { type: "hidden", name: "books.filter.notag", value: "lowtech" }),
    go);
}

// Picture card with a dark caption, e.g. the map preview.
export function card({ href, image, title, sub }) {
  return el("a", { class: "bb-card", href },
    el("img", { src: image, alt: "" }),
    el("span", { class: "bb-card__caption" },
      el("span", {}, el("strong", { class: "bb-card__title" }, title), el("span", { class: "bb-card__sub" }, sub)),
      endArrow()));
}

// variant: "soft", "paper" or "block"; several as "soft block".
export function button({ href, label, iconName, variant, className }) {
  const cls = ["bb-button", ...(variant || "").split(" ").filter(Boolean).map((v) => `bb-button--${v}`), className].filter(Boolean).join(" ");
  return el("a", { class: cls, href }, iconName ? icon(iconName) : null, label);
}

// Header: on phones the nav folds behind a menu button. Call once per page.
export function initHeader(header = document.querySelector(".bb-header")) {
  const nav = header?.querySelector(".bb-nav");
  if (!nav) return;
  nav.id ||= "bb-nav";
  const toggle = el("button", { class: "bb-header__menu", type: "button", "aria-label": "Menu", "aria-expanded": "false", "aria-controls": nav.id }, icon("menu"));
  toggle.addEventListener("click", () => {
    const open = header.classList.toggle("is-open");
    toggle.setAttribute("aria-expanded", String(open));
  });
  nav.addEventListener("click", (e) => { if (e.target.closest("a")) { header.classList.remove("is-open"); toggle.setAttribute("aria-expanded", "false"); } });
  nav.before(toggle);
}

export function strip(links) {
  return el("div", { class: "bb-strip" }, links.map((l) => el("a", { href: l.href }, l.iconName ? icon(l.iconName) : null, l.label)));
}

// Breadcrumb: crumb([{label, href}, "Current"]).
export function crumb(parts) {
  const p = el("p", { class: "bb-crumb" });
  parts.forEach((part, i) => {
    if (i) p.append(" / ");
    p.append(typeof part === "string" ? part : el("a", { href: part.href }, part.label));
  });
  return p;
}

// Links with an optional "No DNS?" fallback address, from web/links.json.
export function linkList(links) {
  return el("ul", { class: "bb-links" }, links.map((l) => el("li", {},
    el("a", { class: "bb-links__main", href: l.url }, l.label),
    l.fallback_url ? el("a", { class: "bb-links__fallback", href: l.fallback_url }, "No DNS? Use " + l.fallback_url.replace(/^https?:\/\//, "")) : null)));
}

export const status = (text) => el("p", { class: "bb-status" }, text);
export const alert = (text) => el("div", { class: "bb-alert", role: "status" }, text);

// Mark the nav link for the current view.
export function setCurrentNav(nav, view) {
  for (const a of nav.querySelectorAll("a[data-view]")) {
    if (a.dataset.view === view) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  }
}
