# STATUS.md

## What was built

**publishing-beyond-kdp-guide** — a plain-English field guide to publishing
wider than Amazon KDP, delivered as Markdown sources plus a local,
tested build script that renders the whole guide as a static HTML site.
Built by Asdale Dynamics, LLC as a small-business/author tool. Complements
**kdp-profit-planner** (the royalty math) and **kdp-interior-templates**
(the print-ready book files).

Content (9 chapters + 3 fill-in worksheets in `docs/`):

- **Rights you keep** — exclusive vs non-exclusive, term/reversion, a
  pre-signing reading checklist.
- **Copyright and ISBNs demystified** — automatic copyright, US
  registration (about $45–65), copyright-page template, KDP-free vs Bowker
  ISBNs ($0 vs about $125 each, cheaper in bulk), imprint-name decision.
- **Wide distribution** — KDP expanded distribution vs IngramSpark,
  wholesale discounts (55% vs 40%), the one-ISBN-one-price rule, a
  compare-costs table, D2D/Lulu aggregator notes.
- **Audiobook routes** — ACX royalty share ($0 upfront / 40% exclusive or
  25% non-exclusive), pay-per-finished-hour ($150–400/hr math with a
  break-even example), self-recording gear list, cheap AI narration
  (Apple/Google) with labeling rules.
- **Getting into libraries** — OverDrive via Draft2Digital, the Indie
  Author Project, Palace Marketplace, Ingram print + an acquisitions
  librarian email template.
- **Direct sales** — Payhip/Gumroad/Shopify/Lulu fee tables at $9.99 and
  $4.99, margin math (85–95%), an in-an-afternoon setup, consignment notes.
- **Author taxes in plain numbers** — 15.3% self-employment tax on 92.35%
  of net profit, effective-combined tables at $5k/$10k/$25k/$50k, quarterly
  estimated payment dates, a deductible-expense list, home-office simplified
  method ($5/sqft, $1,500 cap), economic-nexus sales-tax notes, an Indiana
  state footnote. Educational arithmetic, explicitly not tax advice.
- **Putting it together** — a week-by-week launch sequence, a $0 vs ~$350
  budget comparison, two worked year-one scenarios, a go-wide checklist.
- **Worksheets** — rights map (one-table rights inventory), six-question
  channel decision, one-page cost compare (prefilled worked example with
  break-even units per channel).

All numbers are round planning estimates with "verify current rates on the
platform's page" caveats; no legal/tax advice, no secrets, no personal
data, no network calls anywhere.

Build tooling:

- **`build.py`** — stdlib-only static site generator: docs/*.md ->
  site/*.html with shared navigation, prev/next pager, per-page footer
  (credit + MIT notice), CSS copy, index.html, and internal-link
  validation that fails the build on broken doc links. No external
  packages, no network, no JavaScript in the output.
- **`assets/base.css`** — one stylesheet; print-friendly (hides nav when
  printing worksheets).
- **`tests/test_build.py`** — 52 tests.
- **`site/`** — committed, regenerated output (13 HTML pages + CSS).

## How to run

```bash
python3 build.py --check      # build site/ and verify all expected outputs
python3 -m pytest tests/ -q   # run the 52-test suite
```

Then open `site/index.html` in any browser. Editing any `docs/*.md` and
re-running `build.py` regenerates everything.

## Verification results

- `python3 build.py --check` → **Built 14 files** (base.css, 9 chapter
  pages, 3 worksheet pages, index.html), check passed: every output
  present and non-empty.
- `python3 -m pytest tests/ -q` → **52 passed** in 0.17 s. Coverage:
  - converter unit tests (headings/anchors, paragraph soft-wrap with
    bold/link spanning wrapped lines, inline-code stash protection,
    tables with alignment + ragged rows, blockquotes, checkbox lists,
    ordered/unordered lists with continuation lines, code fences, hr);
  - Markdown -> flat-site link mapping (`worksheets/x.md` ->
    `worksheets-x.html`);
  - hygiene tests (no CJK/fullwidth transcription accidents in docs —
    this caught and verified the fix of several stray-character bugs
    during development);
  - every real document link resolves (mirrors the build's own check);
  - end-to-end builds into a tmp dir: file list, CSS copy, per-page
    copyright/licence footer, nav completeness, pager chaining,
    worksheets rendering, no raw markdown or `.md` links left in HTML;
  - failure paths: broken internal link raises ValueError, missing docs
    dir raises FileNotFoundError.
- `python3 build.py --check` exits 0; the `--out` flag was also exercised
  via tests building into alternate directories.
- No secrets, API keys, or personal data anywhere in the repo (checked by
  hand; only placeholder formatting like the Bowker price table).

## Known gaps

- The site is intentionally JS-free; there is no full-text search.
- The converter supports the Markdown subset used by the guide (it does
  not handle image syntax, nested deeper-than-two-level lists, or
  definition lists; extended tables beyond GFM pipe style are out of
  scope). Unusual docs may need a converter tweak, and there are tests to
  ambush that.
- All platform fees/royalties (KDP, IngramSpark, ACX, D2D, Payhip,
  Gumroad, Lulu, Bowker, Apple/Google narration) are round planning
  numbers, not live quotes; several of them change frequently by design,
  and the guide says so instead of fake-dating itself.
- The tax chapter is US-federal arithmetic plus an Indiana footnote; it
  deliberately does not attempt state-by-state sales-tax registration
  workflows or S-corp scenarios (deferred to a CPA conversation).
- Library-door specifics (Pricing per system, Palace Marketplace
  availability) drift; the guide teaches the doors and points to current
  program pages rather than embedding a rate sheet.
- Companion projects referenced (kdp-profit-planner,
  kdp-interior-templates) are linked as profile URLs; no repo URLs were
  invented.
