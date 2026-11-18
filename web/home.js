// Landing page views: home, all books (#books) and one subject (#subject/<name>).
// Data comes from library.js, building blocks from /brand/ui.js.
import { el, row, index, searchForm, card, button, strip, crumb, linkList, status, alert, setCurrentNav, initHeader } from "/brand/ui.js";
import { subjectByName, loadLibrary, loadLinks, booksIn, visibleSubjects, lib } from "/library.js";

const state = { books: null, dev: false, error: false, chatUrl: null, links: [] };
const page = document.getElementById("page");
const nav = document.querySelector(".bb-nav");
const subjectHref = (name) => "#subject/" + encodeURIComponent(name);

function notices() {
  return [
    state.dev ? alert("DEV MODE: kiwix not reachable at /library/, showing the saved catalog in web/dev/catalog.xml. Book links will not work.") : null,
    state.error ? status("The library isn't responding right now. Search and book links will work again once it's back.") : null,
    !state.books && !state.error ? status("Loading library…") : null,
  ];
}

function homeView() {
  const subjects = visibleSubjects(state.books);
  const survival = subjects.filter((s) => s.survival);
  const more = subjects.filter((s) => !s.survival);
  const total = state.books?.length;

  const shortcuts = el("div", { class: "home-pocket" + (state.chatUrl ? "" : " home-pocket--solo") },
    el("img", { src: "/brand/terrain.jpg", alt: "" }),
    button({ href: "/map/", label: "Offline map", iconName: "map" }),
    state.chatUrl ? button({ href: state.chatUrl, label: "Ask the library", iconName: "ask", variant: "soft" }) : null);

  const content = el("section", {},
    el("h1", { class: "bb-display" }, "Field library"),
    el("p", { class: "bb-lead home-lead" }, "Survival guides, repair manuals and reference books."),
    searchForm(), shortcuts, notices(),
    el("h2", { class: "bb-heading" }, "Survival guides"),
    index(survival.map((s) => row({
      href: subjectHref(s.name), title: s.name, iconName: s.icon, variant: "inline",
      sub: booksIn(state.books, s.name).slice(0, 2).map((b) => b.title).join(" · "),
    }))),
    button({ href: "#books", label: "Browse all books", iconName: "book", variant: "soft block", className: "home-phone-only" }),
    el("h3", { class: "bb-subheading" }, "More subjects"),
    strip(more.map((s) => ({ href: subjectHref(s.name), label: s.name, iconName: s.icon }))),
    state.links.length ? el("div", { class: "home-house" }, el("h3", { class: "bb-subheading" }, "Around the house"), linkList(state.links)) : null);

  const side = el("aside", { class: "home-side" },
    card({ href: "/map/", image: "/brand/terrain.jpg", title: "Offline map", sub: "Browse the world with your location." }),
    el("div", { class: "home-tools" },
      state.chatUrl ? row({ href: state.chatUrl, title: "Ask the library", sub: "Find answers with links to local sources.", iconName: "ask", variant: "tall" }) : null,
      row({ href: "#books", title: "All books", sub: total ? `Browse all ${total} catalog entries.` : "Browse the whole catalog.", iconName: "book", variant: "tall" })));

  return el("div", { class: "home-layout" }, content, side);
}

function booksView() {
  const subjects = visibleSubjects(state.books);
  return el("div", { class: "bb-narrow" },
    crumb([{ label: "Field library", href: "#" }, "Catalog"]),
    el("h1", { class: "bb-display" }, "All books"),
    el("p", { class: "bb-lead" }, state.books ? `${state.books.length} collections across ${subjects.length} subjects` : "Every collection in the library"),
    searchForm(), notices(),
    index(subjects.map((s) => row({
      href: subjectHref(s.name), title: s.name, iconName: s.icon,
      end: state.books ? String(booksIn(state.books, s.name).length) : null,
    }))));
}

function subjectView(subject) {
  const books = booksIn(state.books, subject.name);
  return el("div", { class: "bb-narrow" },
    crumb([{ label: "Field library", href: "#" }, subject.survival ? "Survival guides" : { label: "All books", href: "#books" }]),
    el("h1", { class: "bb-display" }, subject.name),
    el("p", { class: "bb-lead" }, subject.lead),
    notices(),
    index(state.books && !books.length
      ? [status("No books in this subject yet.")]
      : books.map((b) => row({ href: lib(b.href), title: b.title, sub: b.summary, thumb: b.icon ? lib(b.icon) : null }))));
}

function render(moveFocus) {
  const [view, arg = ""] = location.hash.slice(1).split(/\/(.*)/s);
  const subject = view === "subject" ? subjectByName(decodeURIComponent(arg)) : null;
  const [node, current, title] =
    subject ? [subjectView(subject), "books", subject.name]
    : view === "books" || view === "subject" ? [booksView(), "books", "All books"]
    : [homeView(), "home", "Field library"];
  page.replaceChildren(node);
  setCurrentNav(nav, current);
  document.title = `${title} · Bunker Brain`;
  if (moveFocus) { window.scrollTo(0, 0); page.focus(); }
}

initHeader();
window.addEventListener("hashchange", () => render(true));
render();

const [library, links] = await Promise.all([loadLibrary(), loadLinks()]);
Object.assign(state, links);
if (library) Object.assign(state, library); else state.error = true;
if (state.chatUrl) Object.assign(document.getElementById("nav-ask"), { href: state.chatUrl, hidden: false });
render();
