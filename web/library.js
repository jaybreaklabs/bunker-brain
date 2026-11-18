// Library data: subjects and the live Kiwix catalog, with no UI code.
// Edit SUBJECTS to rename, reorder or re-icon a subject; the pages follow.

// Order is display order. "survival" subjects are listed first on the home page;
// the rest go under "More subjects". Names must match "section" in zims.json.
export const SUBJECTS = [
  { name: "Preparedness", icon: "preparedness", survival: true, lead: "Emergency plans, field manuals and self-reliance." },
  { name: "Water & Food", icon: "water", survival: true, lead: "Water treatment, food storage, gardening and cooking." },
  { name: "Repair & Build", icon: "repair", survival: true, lead: "Repair guides, tools, building and appropriate technology." },
  { name: "Medical", icon: "medical", survival: true, lead: "First aid, medicine and health care references." },
  { name: "Power & Energy", icon: "power", lead: "Off-grid power, solar and radio." },
  { name: "Reference", icon: "book", lead: "Encyclopedias, dictionaries, travel guides and source texts." },
  { name: "Learning", icon: "learning", lead: "Questions and answers across science, maths and skills." },
  { name: "Other", icon: "box", lead: "Books not yet sorted into a subject.", hideWhenEmpty: true },
];
export const subjectByName = (name) => SUBJECTS.find((s) => s.name === name);

const CATALOG_URL = "/library/catalog/v2/entries?count=-1";
// DEV ONLY: when the real catalog is unreachable on a local dev host, use a saved
// copy of a live catalog response. Never used in production; don't deploy web/dev/.
const DEV_CATALOG_URL = "/dev/catalog.xml";
const IS_DEV_HOST = ["localhost", "127.0.0.1", "[::1]"].includes(location.hostname);

export const getJSON = (url) => fetch(url).then((r) => (r.ok ? r.json() : null)).catch(() => null);

// Kiwix links in the catalog are absolute paths; add the /library prefix if the server didn't.
export const lib = (href) => (href.startsWith("/library/") ? href : "/library" + href);

async function loadCatalog() {
  let dev = false;
  let res = await fetch(CATALOG_URL).catch(() => null);
  if ((!res || !res.ok) && IS_DEV_HOST) {
    res = await fetch(DEV_CATALOG_URL).catch(() => null);
    dev = true;
  }
  if (!res || !res.ok) throw new Error("catalog unavailable");
  const xml = new DOMParser().parseFromString(await res.text(), "application/xml");
  const text = (e, tag) => e.getElementsByTagName(tag)[0]?.textContent.trim() || "";
  const books = [...xml.getElementsByTagName("entry")].map((e) => ({
    name: text(e, "name"),
    flavour: text(e, "flavour"),
    title: text(e, "title"),
    summary: text(e, "summary"),
    href: e.querySelector('link[type="text/html"]')?.getAttribute("href") || "",
    icon: e.querySelector('link[rel="http://opds-spec.org/image/thumbnail"]')?.getAttribute("href") || "",
  }));
  return { books: books.filter((b) => b.href), dev };
}

function sectionFor(book, zims, prefixes) {
  if (zims) {
    const hits = zims.filter((z) => z.name === book.name && (!z.flavour || !book.flavour || z.flavour === book.flavour));
    const z = hits.find((h) => h.flavour === book.flavour) || hits[0];
    if (z) return { section: z.section, title: z.title || book.title, priority: z.priority ?? 99 };
  }
  let best = "";
  for (const p of Object.keys(prefixes || {})) if (book.name.startsWith(p) && p.length > best.length) best = p;
  return { section: best ? prefixes[best] : "Other", title: book.title, priority: 99 };
}

// Loads the catalog and files each book under a subject.
// Returns { books, dev } or null when the library isn't reachable.
export async function loadLibrary() {
  const [zims, collections, catalog] = await Promise.all([
    getJSON("/zims.json"), getJSON("/collections.json"), loadCatalog().catch(() => null),
  ]);
  if (!catalog) return null;
  const books = catalog.books.map((b) => {
    const m = sectionFor(b, Array.isArray(zims) ? zims : null, collections?.prefixes);
    return { ...b, title: m.title, priority: m.priority, subject: subjectByName(m.section) ? m.section : "Other" };
  });
  return { books, dev: catalog.dev };
}

export const booksIn = (books, subject) => (books || [])
  .filter((b) => b.subject === subject)
  .sort((a, b) => a.priority - b.priority || a.title.localeCompare(b.title));

// Subjects worth showing: all of them, minus "Other" when it's empty.
export const visibleSubjects = (books) =>
  SUBJECTS.filter((s) => !s.hideWhenEmpty || booksIn(books, s.name).length);

// links.json: the entry with id "chat" is the chat app; the rest are "Around the house".
export async function loadLinks() {
  const all = (await getJSON("/links.json")) || [];
  const chat = all.find((l) => l.id === "chat");
  return { chatUrl: chat?.url || null, links: all.filter((l) => l !== chat) };
}
