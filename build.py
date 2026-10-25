#!/usr/bin/env python3
"""Build the static HTML site for publishing-beyond-kdp-guide.

Converts the Markdown under docs/ into site/*.html with shared navigation,
using only the Python standard library. Local-first: no network access, no
external dependencies, nothing leaves the folder.

Usage:
    python3 build.py            # build the site
    python3 build.py --check    # build and verify all expected outputs
    python3 build.py --out DIR  # write to a different directory
"""

import argparse
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
ASSETS = ROOT / "assets"
DEFAULT_OUT = ROOT / "site"

SITE_TITLE = "Publishing Beyond KDP"
SITE_TAGLINE = (
    "Copyright, ISBNs, wide distribution, audiobooks, libraries, and taxes "
    "— in plain English. By Asdale Dynamics, LLC."
)

PAGE_ORDER = [
    ("", "00-start-here.md"),
    ("", "01-rights-you-keep.md"),
    ("", "02-copyright-and-isbns.md"),
    ("", "03-wide-distribution.md"),
    ("", "04-audiobook-routes.md"),
    ("", "05-into-libraries.md"),
    ("", "06-direct-sales.md"),
    ("", "07-author-taxes-plain-numbers.md"),
    ("", "08-putting-it-together.md"),
    ("worksheets", "worksheet-rights-map.md"),
    ("worksheets", "worksheet-channel-decision.md"),
    ("worksheets", "worksheet-cost-compare.md"),
]

PAGE_TITLES = {
    "00-start-here": "Start here",
    "01-rights-you-keep": "Rights you keep",
    "02-copyright-and-isbns": "Copyright and ISBNs",
    "03-wide-distribution": "Wide distribution",
    "04-audiobook-routes": "Audiobook routes",
    "05-into-libraries": "Getting into libraries",
    "06-direct-sales": "Direct sales",
    "07-author-taxes-plain-numbers": "Author taxes in plain numbers",
    "08-putting-it-together": "Putting it together",
    "worksheets-worksheet-rights-map": "Worksheet: rights map",
    "worksheets-worksheet-channel-decision": "Worksheet: channel decision",
    "worksheets-worksheet-cost-compare": "Worksheet: cost compare",
}


# ---------------------------------------------------------------------------
# Markdown -> HTML (small, purpose-built converter)
# ---------------------------------------------------------------------------

def _slugify(text: str) -> str:
    """Heading text -> anchor id."""
    slug = re.sub(r"<[^>]+>", "", text)
    slug = re.sub(r"[^a-z0-9 -]", "", slug.lower())
    slug = re.sub(r"[ -]+", "-", slug.strip())
    return "h-" + slug if slug else "h"


def _inline(text: str) -> str:
    """Render inline markdown (bold, italic, code, links) to HTML.

    ``text`` must already be HTML-escaped; inline-code spans are stashed with
    sentinel markers so formatting never applies inside them.
    """
    stashed: list = []

    def stash_code(match):
        stashed.append(match.group(1))
        return f"\x00{len(stashed) - 1}\x00"

    text = re.sub(r"`([^`]+)`", stash_code, text)

    def render_link(match):
        label, target = match.group(1), match.group(2).strip()
        if target.endswith(".md") and not re.match(r"^[a-z]+://", target):
            # docs-relative path -> flat site page:
            # worksheets/x.md -> worksheets-x.html
            target = target[:-3].replace("/", "-") + ".html"
        return f'<a href="{html.escape(target, quote=True)}">{label}</a>'

    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", render_link, text)

    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text, flags=re.S)
    text = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", text)

    def unstash(match):
        # content arrives pre-escaped by the caller
        return f"<code>{stashed[int(match.group(1))]}</code>"

    return re.sub(r"\x00(\d+)\x00", unstash, text)


def md_to_html(md_text: str) -> str:
    """Convert the subset of Markdown used in docs/ into HTML."""
    lines = md_text.split("\n")
    out: list = []
    paragraph: list = []      # raw text fragments of the current paragraph
    list_tag = None           # tag ("ul"/"ol") of the currently open list
    li_parts: list = None     # raw text fragments of the current list item
    li_checked = False
    last_kind = None          # "ul" or "ol", remembered when list continues

    def close_paragraph() -> None:
        if paragraph:
            text = html.escape(" ".join(paragraph))
            out.append(f"<p>{_inline(text)}</p>")
            paragraph.clear()

    def flush_item() -> None:
        nonlocal li_parts, li_checked
        if li_parts is not None:
            text = html.escape(" ".join(li_parts))
            if li_checked:
                out.append(f'<li class="checked">{_inline(text)}</li>')
            else:
                out.append(f"<li>{_inline(text)}</li>")
            li_parts = None
            li_checked = False

    def close_list() -> None:
        nonlocal list_tag
        if list_tag:
            flush_item()
            out.append(f"</{list_tag}>")
            list_tag = None

    def open_list(tag: str) -> None:
        nonlocal list_tag, last_kind
        flush_item()
        if list_tag != tag:
            close_paragraph()
            if list_tag is not None:
                out.append(f"</{list_tag}>")
            out.append(f"<{tag}>")
            list_tag = tag
        last_kind = tag

    def close_blocks() -> None:
        close_paragraph()
        close_list()

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Fenced code block ---------------------------------------------------
        if stripped.startswith("```") or stripped.startswith("~~~"):
            close_blocks()
            i += 1
            block = []
            while i < len(lines) and not (
                lines[i].strip().startswith("```")
                or lines[i].strip().startswith("~~~")
            ):
                block.append(lines[i])
                i += 1
            i += 1  # skip the closing fence
            out.append(
                "<pre><code>" + html.escape("\n".join(block)) + "</code></pre>"
            )
            continue

        # Heading ----------------------------------------------------------------
        match = re.match(r"^(#{1,4})\s+(.*)$", line)
        if match:
            close_blocks()
            level = len(match.group(1))
            body = _inline(html.escape(match.group(2)))
            out.append(f'<h{level} id="{_slugify(body)}">{body}</h{level}>')
            i += 1
            continue

        # Horizontal rule --------------------------------------------------------
        if re.fullmatch(r"(\*\*\*|---|___)\s*", stripped):
            close_blocks()
            out.append("<hr>")
            i += 1
            continue

        # Table (GFM pipe style) -----------------------------------------------
        if (
            stripped.startswith("|") and stripped.endswith("|")
            and i + 1 < len(lines)
            and re.fullmatch(r"\|[\s\-:|]+\|", lines[i + 1].strip())
        ):
            close_blocks()
            header = [c.strip() for c in stripped.strip("|").split("|")]
            separator = stripped  # keep reference for linters; unused value
            del separator
            aligns = [
                c.strip() for c in lines[i + 1].strip().strip("|").split("|")
            ]
            out.append("<table><thead><tr>")
            for idx, cell in enumerate(header):
                align = ""
                if idx < len(aligns):
                    a = aligns[idx]
                    if a.startswith(":") and a.endswith(":"):
                        align = ' style="text-align:center"'
                    elif a.endswith(":"):
                        align = ' style="text-align:right"'
                out.append(f"<th{align}>{_inline(html.escape(cell))}</th>")
            out.append("</tr></thead><tbody>")
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                row = lines[i].strip().strip("|")
                cells = [c.strip() for c in row.split("|")]
                out.append("<tr>")
                for idx in range(len(header)):
                    cell = cells[idx] if idx < len(cells) else ""
                    out.append(f"<td>{_inline(html.escape(cell))}</td>")
                out.append("</tr>")
                i += 1
            out.append("</tbody></table>")
            continue

        # Blockquote -------------------------------------------------------------
        if stripped.startswith(">"):
            close_blocks()
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip().lstrip(">").strip())
                i += 1
            body = _inline(html.escape(" ".join(q for q in quote if q)))
            out.append(f"<blockquote>{body}</blockquote>")
            continue

        # Checkbox items (task lists) --------------------------------------------
        check = re.match(r"^(\s*)[-*] \[([ xX])\]\s+(.*)$", line)
        if check:
            paragraph.clear()
            open_list("ul")
            last_kind = "ul"
            li_checked = (check.group(2).lower() == "x")
            li_parts = [check.group(3).strip()]
            i += 1
            continue

        # Unordered / ordered list -------------------------------------------------
        ul = re.match(r"^(\s*)[-*] (?!\[)(.*)$", line)
        ol = re.match(r"^(\s*)\d+\.\s+(.*)$", line)
        if ul or ol:
            kind = "ul" if ul else "ol"
            open_list(kind)
            last_kind = kind
            li_checked = False
            li_parts = [(ul or ol).group(2).strip()]
            i += 1
            continue

        # Indented continuation of the current list item ----------------------------
        if list_tag is not None and li_parts is not None and re.match(r"^\s{2,}\S", line):
            li_parts.append(stripped)
            i += 1
            continue

        # Blank line: close open structures --------------------------------------
        if not stripped:
            close_blocks()
            i += 1
            continue

        # Ordinary paragraph line (inline runs once on the joined text) ------------
        paragraph.append(stripped)
        i += 1

    close_blocks()
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Page assembly
# ---------------------------------------------------------------------------

def page_slug(subdir: str, filename: str) -> str:
    base = Path(filename).stem
    return subdir + "-" + base if subdir else base


def nav_html(active_slug: str) -> str:
    parts = ['<nav class="pages">']
    main_pages = PAGE_ORDER[:9]
    worksheets = PAGE_ORDER[9:]
    for idx, (subdir, filename) in enumerate(main_pages):
        slug = page_slug(subdir, filename)
        here = ' class="here"' if slug == active_slug else ""
        parts.append(
            f'<a href="{slug}.html"{here}>{idx + 1}. {PAGE_TITLES[slug]}</a><br>'
        )
    parts.append("<br><strong>Worksheets</strong><br>")
    for subdir, filename in worksheets:
        slug = page_slug(subdir, filename)
        here = ' class="here"' if slug == active_slug else ""
        parts.append(f'<a href="{slug}.html"{here}>{PAGE_TITLES[slug]}</a><br>')
    parts.append("</nav>")
    return "".join(parts)


def pager_html(active_slug: str) -> str:
    slugs = [page_slug(s, f) for s, f in PAGE_ORDER]
    if active_slug not in slugs:
        return ""
    idx = slugs.index(active_slug)
    parts = []
    if idx > 0:
        prev = slugs[idx - 1]
        parts.append(f'<a href="{prev}.html">&larr; {PAGE_TITLES[prev]}</a>')
    else:
        parts.append("<span></span>")
    if idx < len(slugs) - 1:
        nxt = slugs[idx + 1]
        parts.append(f'<a href="{nxt}.html">{PAGE_TITLES[nxt]} &rarr;</a>')
    else:
        parts.append("<span></span>")
    return "".join(parts)


def compose_page(active_slug: str, body_html: str) -> str:
    title = PAGE_TITLES.get(active_slug, active_slug)
    nav = nav_html(active_slug)
    pager = pager_html(active_slug)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} - {SITE_TITLE}</title>
<meta name="description" content="{html.escape(SITE_TAGLINE, quote=True)}">
<link rel="stylesheet" href="base.css">
</head>
<body>
<div class="wrap">
<header class="site">
  <div class="brand">Asdale Dynamics, LLC &middot; author field guides</div>
  <h1>{html.escape(SITE_TITLE)}</h1>
  {nav}
</header>
<article>
{body_html}
</article>
<nav class="pager" aria-label="Next and previous page">{pager}</nav>
<footer class="site">
  Publishing Beyond KDP &middot; <strong>Copyright (c) 2026 Asdale Dynamics, LLC</strong> &middot; MIT licensed &middot; educational guide, not legal or tax advice &middot; built locally, no tracking.
</footer>
</div>
</body>
</html>
"""


def build_site(docs_dir: Path = None, out_dir: Path = None) -> list:
    """Build the whole site. Returns the list of files written."""
    docs_dir = docs_dir if docs_dir is not None else DOCS
    out_dir = out_dir if out_dir is not None else DEFAULT_OUT

    if not (docs_dir / "00-start-here.md").exists():
        raise FileNotFoundError(f"no docs/00-start-here.md under {docs_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)
    written = []

    css_out = out_dir / "base.css"
    css_out.write_text(
        (ASSETS / "base.css").read_text(encoding="utf-8"), encoding="utf-8"
    )
    written.append(css_out)

    renderings = {}
    for subdir, filename in PAGE_ORDER:
        slug = page_slug(subdir, filename)
        path = docs_dir / subdir / filename if subdir else docs_dir / filename
        if not path.exists():
            continue  # build whatever subset of pages the docs dir has
        renderings[slug] = (path, md_to_html(path.read_text(encoding="utf-8")))

    valid_targets = {f"{slug}.html" for slug in renderings} | {"base.css"}
    for slug, (path, rendered) in renderings.items():
        for match in re.finditer(r"href=\"([^\"]+)\"", rendered):
            target = match.group(1)
            if re.match(r"^[a-z]+:", target) or target in valid_targets:
                continue
            # Bare sibling references inside worksheets/ (e.g.
            # "worksheet-cost-compare.html") resolve to the flat alias
            # "worksheets-worksheet-cost-compare.html" used by the site.
            if "worksheets-" + target in valid_targets:
                continue
            raise ValueError(f"{path.name}: broken internal link -> {target}")

    for slug, (path, rendered) in renderings.items():
        out = out_dir / f"{slug}.html"
        out.write_text(compose_page(slug, rendered), encoding="utf-8")
        written.append(out)

    index = out_dir / "index.html"
    index.write_text(
        (out_dir / "00-start-here.html").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    written.append(index)
    return written


def check_site(docs_dir: Path = None, out_dir: Path = None) -> list:
    """Build, then verify every expected file exists and is non-empty."""
    written = build_site(docs_dir=docs_dir, out_dir=out_dir)
    for path in written:
        if not path.exists() or path.stat().st_size == 0:
            raise RuntimeError(f"bad output: {path}")
    return written


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Build the publishing-beyond-kdp-guide static site."
    )
    parser.add_argument(
        "--out", type=Path, default=DEFAULT_OUT,
        help="output directory (default: site/)",
    )
    parser.add_argument(
        "--check", action="store_true",
        help="build, then verify every expected file exists",
    )
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    docs_dir = DOCS
    if not (docs_dir / "00-start-here.md").exists():
        cwd = Path.cwd()
        if (cwd / "docs" / "00-start-here.md").exists():
            docs_dir = cwd / "docs"
        else:
            print("error: could not find docs/00-start-here.md", file=sys.stderr)
            return 1

    try:
        written = check_site(docs_dir=docs_dir, out_dir=args.out)
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        print(f"build failed: {exc}", file=sys.stderr)
        return 1

    if not args.quiet:
        print(f"Built {len(written)} files into {args.out}:")
        for path in written:
            print(f"  {path.relative_to(args.out.resolve().parent)}")
        if args.check:
            print("check: all expected outputs present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
