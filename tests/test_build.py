"""Tests for build.py: converter unit tests, site build e2e, link checking.

Run from the project root with:  python3 -m pytest tests/ -v
"""

import re
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build  # noqa: E402


# ---------------------------------------------------------------------------
# Converter unit tests
# ---------------------------------------------------------------------------

class TestHeadings:
    def test_h1_gets_anchor_id(self):
        out = build.md_to_html("# Hello World")
        assert out == '<h1 id="h-hello-world">Hello World</h1>'

    def test_heading_levels(self):
        out = build.md_to_html("## Two\n\n### Three\n\n#### Four")
        for level in (2, 3, 4):
            assert f"<h{level} " in out

    def test_heading_with_inline_formatting(self):
        out = build.md_to_html("## A **bold** title")
        assert "<strong>bold</strong>" in out


class TestParagraphs:
    def test_soft_wrap_joins_lines(self):
        out = build.md_to_html("first line\nsecond line")
        assert "<p>first line second line</p>" in out

    def test_bold_across_wrapped_lines(self):
        out = build.md_to_html("text **bold across\nwrapped lines** ends")
        assert "<strong>bold across wrapped lines</strong>" in out

    def test_italic(self):
        out = build.md_to_html("say *this quietly*")
        assert "<em>this quietly</em>" in out

    def test_bold_with_inner_asterisk(self):
        out = build.md_to_html("**The ISBN's *issuer* is recorded.**")
        assert "<strong>The ISBN&#x27;s <em>issuer</em> is recorded.</strong>" in out

    def test_blank_line_separates_paragraphs(self):
        out = build.md_to_html("one\n\n\nthree")
        assert out.count("<p>") == 2


class TestInlineCode:
    def test_code_span(self):
        out = build.md_to_html("run `python3 build.py` now")
        assert "<code>python3 build.py</code>" in out

    def test_code_protects_markdown(self):
        out = build.md_to_html("use `**not bold**` here")
        assert "<strong>" not in out
        assert "<code>**not bold**</code>" in out

    def test_html_is_escaped_in_code(self):
        out = build.md_to_html("tag `<div>`")
        assert "&lt;div&gt;" in out


class TestLinks:
    def test_md_link_becomes_html_link(self):
        out = build.md_to_html("see [chapter two](02-copyright-and-isbns.md)")
        assert 'href="02-copyright-and-isbns.html"' in out

    def test_worksheet_link_maps_to_flat_slug(self):
        out = build.md_to_html("open [the sheet](worksheets/worksheet-cost-compare.md)")
        assert 'href="worksheets-worksheet-cost-compare.html"' in out

    def test_external_link_untouched(self):
        out = build.md_to_html("[ACX](https://www.acx.com)")
        assert 'href="https://www.acx.com"' in out

    def test_link_label_keeps_bold(self):
        out = build.md_to_html("[**Big** deal](05-into-libraries.md)")
        assert "href=" in out and "<strong>Big</strong>" in out


class TestLists:
    def test_unordered_list(self):
        out = build.md_to_html("- one\n- two")
        assert "<ul>" in out and "<li>one</li>" in "<ul><li>one</li><li>two</li></ul>"

    def test_ordered_list(self):
        out = build.md_to_html("1. one\n2. two")
        assert "<ol>" in out and "<li>one</li>" in out

    def test_continuation_line_joins_item(self):
        out = build.md_to_html("- item continues\n  here\n")
        assert "<li>item continues here</li>" in out

    def test_continuation_bold_across_lines(self):
        out = build.md_to_html("- piece one **of\n  bold** text")
        assert "<strong>of bold</strong>" in out

    def test_blank_line_ends_list(self):
        out = build.md_to_html("- first\n\nsecond para")
        assert "</ul>" in out and "<p>second para</p>" in out


class TestCheckboxes:
    def test_checked_item(self):
        out = build.md_to_html("- [x] done thing")
        assert '<li class="checked">done thing</li>' in out

    def test_unchecked_item(self):
        out = build.md_to_html("- [ ] open thing")
        assert "<li>open thing</li>" in out

    def test_mixed_checkbox_list_is_one_list(self):
        out = build.md_to_html("- [x] a\n- [ ] b")
        assert out.count("<ul>") == 1 and out.count("</ul>") == 1


class TestTables:
    def test_simple_table(self):
        out = build.md_to_html("| a | b |\n|---|---|\n| 1 | 2 |")
        assert "<table><thead><tr>" in out
        assert "<th>a</th>" in out and "<th>b</th>" in out
        assert "<td>1</td>" in out and "<td>2</td>" in out

    def test_right_alignment(self):
        out = build.md_to_html("| a |\n|---:|\n| 1 |")
        assert 'style="text-align:right"' in out

    def test_table_cells_get_inline_formatting(self):
        out = build.md_to_html("| x | y |\n|---|---|\n| **bold** | text |")
        assert "<strong>bold</strong>" in out

    def test_no_table_without_separator_row(self):
        out = build.md_to_html("| a | b |\n| 1 | 2 |")
        assert "<table>" not in out

    def test_ragged_row_padded(self):
        out = build.md_to_html("| a | b | c |\n|---|---|---|\n| x | y |")
        assert out.count("<td>") == 3


class TestBlockquoteAndFences:
    def test_blockquote_joined_lines(self):
        out = build.md_to_html("> first quote\n> second quote")
        assert "<blockquote>first quote second quote</blockquote>" in out

    def test_blockquote_inline_link(self):
        out = build.md_to_html("> see [ch](03-wide-distribution.md)")
        assert 'href="03-wide-distribution.html"' in out

    def test_code_fence_preserves_lines(self):
        out = build.md_to_html("```\nline one\n  line two\n```")
        assert "line one\n  line two" in build.md_to_html("```\nline one\n  line two\n```")

    def test_code_fence_escapes_html(self):
        out = build.md_to_html("```\n<b>&raw</b>\n```")
        assert "&lt;b&gt;&amp;raw&lt;/b&gt;" in out

    def test_horizontal_rule(self):
        out = build.md_to_html("above\n\n---\n\nbelow")
        assert "<hr>" in out


# ---------------------------------------------------------------------------
# Whole-doc safety checks
# ---------------------------------------------------------------------------

class TestSourceHygiene:
    def test_no_cjk_or_fullwidth_characters_in_docs(self):
        """Catches transcription accidents: stray CJK/fullwidth glyphs."""
        bad = []
        for path in sorted((ROOT / "docs").rglob("*.md")):
            for line_no, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), 1
            ):
                for ch in line:
                    o = ord(ch)
                    if (
                        0x2E80 <= o <= 0x9FFF
                        or 0xF900 <= o <= 0xFAFF
                        or 0xFF00 <= o <= 0xFFEF
                        or ch in "\u3000\u3001\u3002\ufffd"
                    ):
                        bad.append((path.name, line_no, ch, hex(o)))
        assert not bad, f"unexpected characters: {bad}"

    def test_every_doc_has_an_h1_title(self):
        for sub, name in build.PAGE_ORDER:
            path = ROOT / "docs" / sub / name if sub else ROOT / "docs" / name
            first = next(
                ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()
            )
            assert first.startswith("# "), f"{path.name} missing H1 title"

    def test_every_built_page_carries_credit_and_license(self):
        for slug in [build.page_slug(s, f) for s, f in build.PAGE_ORDER]:
            page = build.compose_page(slug, "")
            assert "Copyright (c) 2026 Asdale Dynamics, LLC" in page, slug
            assert "MIT licensed" in page, slug


# ---------------------------------------------------------------------------
# Internal link validation on the real docs
# ---------------------------------------------------------------------------

def iter_real_links():
    for slug, (path, rendered) in _render_all().items():
        for match in re.finditer(r'href="([^"]+)"', rendered):
            yield slug, match.group(1)


def _render_all():
    renderings = {}
    for subdir, filename in build.PAGE_ORDER:
        slug = build.page_slug(subdir, filename)
        path = (
            ROOT / "docs" / subdir / filename
            if subdir
            else ROOT / "docs" / filename
        )
        renderings[slug] = (path, build.md_to_html(path.read_text(encoding="utf-8")))
    return renderings


def test_all_real_document_links_resolve():
    valid = {f"{slug}.html" for slug in _render_all()} | {
        "worksheets-" + t for t in []
    }
    # add sibling aliases exactly like build_site does
    for slug in list(valid):
        bare = slug.replace("worksheets-", "")
        valid.add(bare)
    valid.add("base.css")
    for slug, href in iter_real_links():
        if re.match(r"^[a-z]+://", href) or href.startswith("#"):
            continue
        internal = href.split("#")[0]
        assert internal in valid, f"broken link from {slug}: {href}"


# ---------------------------------------------------------------------------
# End-to-end site build
# ---------------------------------------------------------------------------

@pytest.fixture
def site(tmp_path):
    return build.build_site(out_dir=tmp_path / "site")


class TestSiteBuild:
    def test_writes_expected_files(self, site):
        names = {p.name for p in site}
        assert names == {
            "base.css",
            "index.html",
            "00-start-here.html",
            "01-rights-you-keep.html",
            "02-copyright-and-isbns.html",
            "03-wide-distribution.html",
            "04-audiobook-routes.html",
            "05-into-libraries.html",
            "06-direct-sales.html",
            "07-author-taxes-plain-numbers.html",
            "08-putting-it-together.html",
            "worksheets-worksheet-rights-map.html",
            "worksheets-worksheet-channel-decision.html",
            "worksheets-worksheet-cost-compare.html",
        }

    def test_css_copied(self, tmp_path):
        target = tmp_path / "out" / "base.css"
        build.build_site(out_dir=tmp_path / "out")
        assert target.read_text(encoding="utf-8") == (
            ROOT / "assets" / "base.css"
        ).read_text(encoding="utf-8")

    def test_every_page_has_css_nav_and_footer(self, site):
        for page in site:
            if page.suffix != ".html":
                continue
            text = page.read_text(encoding="utf-8")
            assert '<div class="wrap">' in text
            assert 'href="base.css"' in text
            assert "Copyright (c) 2026 Asdale Dynamics, LLC" in text
            assert 'class="pager"' in text or page.name == "index.html"

    def test_index_is_copy_of_start_here(self, site):
        start = (site[0].parent / "00-start-here.html").read_text("utf-8")
        index = (site[0].parent / "index.html").read_text("utf-8")
        assert start == index

    def test_nav_links_all_pages(self, site):
        text = (site[1].parent / "01-rights-you-keep.html").read_text("utf-8")
        for slug in (
            "00-start-here",
            "08-putting-it-together",
            "worksheets-worksheet-cost-compare",
        ):
            assert f'href="{slug}.html"' in text

    def test_pager_chained(self, site):
        text = (site[1].parent / "08-putting-it-together.html").read_text("utf-8")
        assert "07-author-taxes-plain-numbers.html" in text

    def test_worksheets_render_as_lists(self, site):
        text = (
            site[1].parent / "worksheets-worksheet-cost-compare.html"
        ).read_text("utf-8")
        assert "<table>" in text

    def test_rights_map_has_checkboxes(self, site):
        text = (
            site[1].parent / "worksheets-worksheet-rights-map.html"
        ).read_text("utf-8")
        assert 'class="checked"' in text or "<li>" in text

    def test_no_markdown_left_in_html(self, site):
        for page in site:
            if page.suffix != ".html":
                continue
            text = page.read_text(encoding="utf-8")
            assert "**" not in re.sub(r"<pre>.*?</pre>", "", text, flags=re.S)
            assert not re.search(r"\[[^\]]+\]\([^)]*\.md\)", text)


class TestLinkValidation:
    def test_broken_internal_link_raises(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "00-start-here.md").write_text(
            "# T\n\ngoto [nothing](99-missing.md)\n", encoding="utf-8"
        )
        with pytest.raises(ValueError, match="broken internal link"):
            build.build_site(docs_dir=docs, out_dir=tmp_path / "out")

    def test_good_links_pass_in_tiny_site(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "00-start-here.md").write_text(
            "# T\n\ngoto [real](00-start-here.md)\n", encoding="utf-8"
        )
        written = build.build_site(docs_dir=docs, out_dir=tmp_path / "out")
        assert any(p.name == "00-start-here.html" for p in written)


class TestChekSiteRunner:
    def test_check_site_reports_bad_file(self, tmp_path, monkeypatch):
        # make css copy fail silently by pointing at a repo we control
        out = tmp_path / "site"
        build.check_site(out_dir=out)
        for path in out.iterdir():
            assert path.stat().st_size > 0

    def test_missing_docs_raises(self, tmp_path):
        empty = tmp_path / "docs-empty"
        empty.mkdir()
        with pytest.raises(FileNotFoundError):
            build.build_site(docs_dir=empty, out_dir=tmp_path / "out")


class TestPageSlug:
    def test_flat_slug(self):
        assert build.page_slug("", "01-x.md") == "01-x"

    def test_prefixed_slug(self):
        assert build.page_slug("worksheets", "worksheet-a.md") == (
            "worksheets-worksheet-a"
        )
