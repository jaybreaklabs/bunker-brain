"""
title: Offline Library Search
description: Full-text search of the household Kiwix library (kiwix-serve), returning article text with numbered, clickable citations.
version: 0.1.0
license: MIT
"""

import asyncio
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

from pydantic import BaseModel, Field

TIMEOUT = 15  # seconds per HTTP request
ATOM = "{http://www.w3.org/2005/Atom}"
STOPWORDS = {"the", "and", "for", "with", "how", "what", "does", "from", "that", "this", "are", "can",
             "you", "your", "use", "using", "into", "about", "should", "when", "why", "which"}

# Elements whose whole subtree is page chrome, not article text.
SKIP_TAGS = {"script", "style", "noscript", "head", "nav", "header", "footer",
             "template", "svg", "button", "form", "select", "iframe"}
BLOCK_TAGS = {"p", "div", "br", "li", "ul", "ol", "tr", "table", "section",
              "article", "main", "blockquote", "pre", "dd", "dt", "dl",
              "h1", "h2", "h3", "h4", "h5", "h6", "figcaption", "hr"}


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TAGS:
            self.skip += 1
        elif tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_startendtag(self, tag, attrs):
        if tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS:
            self.skip = max(0, self.skip - 1)
        elif tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def html_to_text(html: str) -> str:
    """Readable text from an article page: chrome dropped, whitespace collapsed."""
    p = _TextExtractor()
    p.feed(html)
    p.close()
    lines = (re.sub(r"[ \t\r\f\v]+", " ", ln).strip() for ln in "".join(p.parts).split("\n"))
    return "\n".join(ln for ln in lines if ln)


def trim(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    cut = text[:limit]
    space = cut.rfind(" ")
    return (cut[:space] if space > limit * 0.8 else cut).rstrip() + " ..."


def excerpt(text: str, query: str, limit: int) -> str:
    """The lines that match the query (plus a little context), in page order, within limit.
    Long pages bury the answer mid-article (a dosage table, a step list), so the head alone misses it."""
    if len(text) <= limit:
        return text
    lines = text.split("\n")
    low = [ln.lower() for ln in lines]
    terms = {w for w in re.findall(r"\w+", query.lower()) if len(w) > 2 and w not in STOPWORDS}
    # A term on every line ("water" in a water article) says little; a rare one ("bleach") says a lot.
    weight = {t: 1 / n for t in terms if (n := sum(t in ln for ln in low))}
    scores = [sum(w for t, w in weight.items() if t in ln) for ln in low]

    def window(i):  # heading above, rows/steps below
        return range(max(0, i - 2), min(len(lines), i + 4))

    # Rank whole windows, so a real section beats a lone table-of-contents line.
    ranked = sorted((i for i, s in enumerate(scores) if s), key=lambda i: (-sum(scores[j] for j in window(i)), i))
    keep, used = set(), 0
    for i in ranked:
        for j in window(i):
            if j not in keep:
                keep.add(j)
                used += len(lines[j]) + 1
        if used >= limit:
            break
    if not keep:
        return trim(text, limit)
    out, prev = [], -1
    for j in sorted(keep):
        if prev != -1 and j != prev + 1:
            out.append("...")
        out.append(lines[j])
        prev = j
    return trim("\n".join(out), limit)


def parse_search(xml_text: str) -> list:
    """kiwix-serve /search?format=xml (RSS) -> [{title, link, book, book_name, snippet}]."""
    results = []
    for item in ET.fromstring(xml_text).iter("item"):
        link = (item.findtext("link") or "").strip()
        desc = item.find("description")
        snippet = " ".join("".join(desc.itertext()).split()) if desc is not None else ""
        # Links look like <root>/content/<book-id>/<path>; the book id is the segment after "content".
        segs = link.split("/")
        book_name = segs[segs.index("content") + 1] if "content" in segs[:-1] else ""
        results.append({
            "title": (item.findtext("title") or "").strip(),
            "link": link,
            "book": (item.findtext("book/title") or "").strip(),
            "book_name": book_name,
            "snippet": snippet,
        })
    return results


def parse_catalog(xml_text: str) -> list:
    """OPDS /catalog/v2/entries -> [{name, title, summary, articles}]."""
    return [{
        "name": (e.findtext(ATOM + "name") or "").strip(),
        "title": (e.findtext(ATOM + "title") or "").strip(),
        "summary": (e.findtext(ATOM + "summary") or "").strip(),
        "articles": (e.findtext(ATOM + "articleCount") or "").strip(),
    } for e in ET.fromstring(xml_text).iter(ATOM + "entry")]


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "offline-library-tool"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read().decode(r.headers.get_content_charset() or "utf-8", "replace")


def _http_error(base: str, err: Exception) -> str:
    if isinstance(err, urllib.error.HTTPError):
        detail = err.read().decode("utf-8", "replace")
        m = re.findall(r"<detail>(.*?)</detail>", detail)
        return f"The offline library returned HTTP {err.code}: {' '.join(m) or err.reason}"
    return (f"The offline library at {base} could not be reached ({err}). "
            "Tell the user the library is unavailable right now; do not answer from memory as if it were a library source.")


class Tools:
    class Valves(BaseModel):
        KIWIX_BASE_URL: str = Field(
            "http://kiwix:8080",
            description="Internal kiwix-serve URL this server can reach (include the URL root, e.g. .../library, if kiwix-serve uses --urlRootLocation).")
        PUBLIC_BASE_URL: str = Field(
            "https://wiki.example.com/library",
            description="Base URL users click in citations; the article path is appended.")
        MAX_RESULTS: int = Field(5, description="Number of search results to fetch and return.")
        MAX_CHARS_PER_ARTICLE: int = Field(3000, description="Character budget per article.")
        BOOKS: str = Field(
            "",
            description="Optional comma-separated book names (from list_books) to restrict search to. Empty = all books.")
        EXCLUDE_TAGS: str = Field(
            "lowtech",
            description="Comma-separated catalog tags to leave out of search. kiwix-serve refuses to search books in "
                        "different languages together, so multilingual books (e.g. Low-tech Magazine, tag 'lowtech') go here.")

    def __init__(self):
        self.valves = self.Valves()

    def _public_url(self, link: str) -> str:
        # Strip the internal URL root from the result link, then hang it off the public base.
        root = urllib.parse.urlparse(self.valves.KIWIX_BASE_URL).path.rstrip("/")
        if root and link.startswith(root + "/"):
            link = link[len(root):]
        return self.valves.PUBLIC_BASE_URL.rstrip("/") + link

    async def search_library(self, query: str, __event_emitter__=None) -> str:
        """
        Search the offline library (Wikipedia, Wikivoyage, survival, repair and medical collections) and return the most relevant article text with numbered citations.
        Use this for factual questions the library may cover, then answer from the returned text and cite sources as [n].
        :param query: Search words, e.g. "boil water" or "splint broken arm".
        :return: Article excerpts with numbered sources and their URLs.
        """
        base = self.valves.KIWIX_BASE_URL.rstrip("/")
        n = max(1, int(self.valves.MAX_RESULTS))
        params = [("pattern", query), ("format", "xml"), ("pageLength", str(n))]
        params += [("books.filter.name", b.strip()) for b in self.valves.BOOKS.split(",") if b.strip()]
        notags = ";".join(t.strip() for t in self.valves.EXCLUDE_TAGS.split(",") if t.strip())
        if notags:
            params.append(("books.filter.notag", notags))
        try:
            hits = parse_search(await asyncio.to_thread(_get, f"{base}/search?{urllib.parse.urlencode(params)}"))
        except (urllib.error.URLError, OSError, ValueError) as e:  # URLError covers HTTPError; OSError covers timeouts
            return _http_error(base, e)
        except ET.ParseError as e:
            return f"The offline library returned a response that could not be parsed ({e})."

        if not hits:
            return (f'The offline library has no results for "{query}". '
                    "Tell the user the library has nothing on this; do not invent library citations.")

        blocks = []
        for i, h in enumerate(hits[:n], 1):
            url = self._public_url(h["link"])
            try:
                text = html_to_text(await asyncio.to_thread(_get, urllib.parse.urljoin(base + "/", h["link"])))
            except (urllib.error.URLError, OSError, ValueError):
                text = h["snippet"]  # ponytail: snippet fallback if one article fails to load
            text = excerpt(text, query, int(self.valves.MAX_CHARS_PER_ARTICLE))
            blocks.append(f"[{i}] {h['title']} ({h['book']})\nURL: {url}\n{text}")
            if __event_emitter__:
                await __event_emitter__({
                    "type": "citation",
                    "data": {
                        "document": [text],
                        "metadata": [{"source": url, "name": f"[{i}] {h['title']}", "url": url}],
                        "source": {"name": f"[{i}] {h['title']} ({h['book']})", "url": url},
                    },
                })

        header = (f'Offline library results for "{query}".\n'
                  "Answer only from these sources and cite them inline as [n], listing the URLs used at the end. "
                  "If none of them is relevant, say the offline library has nothing relevant instead of guessing. "
                  "For medical or survival topics, present the answer as guidance to these sources, not as authority, "
                  "and tell the user to check the source and seek professional help where possible.\n")
        return header + "\n\n".join(blocks)

    async def list_books(self) -> str:
        """
        List the books (ZIM collections) in the offline library, with the names usable for search restriction.
        :return: One line per book: name, title, article count, summary.
        """
        base = self.valves.KIWIX_BASE_URL.rstrip("/")
        try:
            books = parse_catalog(await asyncio.to_thread(_get, f"{base}/catalog/v2/entries?count=-1"))
        except (urllib.error.URLError, OSError, ValueError) as e:
            return _http_error(base, e)
        except ET.ParseError as e:
            return f"The offline library returned a catalog that could not be parsed ({e})."
        if not books:
            return "The offline library has no books loaded."
        return "\n".join(f"- {b['name']}: {b['title']} ({b['articles']} articles) - {b['summary']}" for b in books)
