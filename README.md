# Publishing Beyond KDP

A plain-English field guide to publishing **wider** than Amazon KDP — the
copyright and ISBN decisions, the wide-print and library channels, the
audiobook routes, direct sales, and the tax math — with decision worksheets
and compare-costs tables, plus a small local build script that renders the
whole guide as a static HTML site.

Written in the same beginner-first voice as *The Massive AI Manual* and
[dylanasdale.github.io](https://dylanasdale.github.io): clear, warm, step by
step, never condescending. Built by **Asdale Dynamics, LLC** — beginner
friendly AI education, books and guides, and practical tools. MIT licensed
(see `LICENSE`).

Everything runs locally. No accounts, no network calls, no API keys, no
tracking, no data leaves the folder. No legal or tax advice anywhere — the
guide teaches the map; professionals check your actual paperwork.

## What's inside

Nine chapters and three fill-in worksheets:

| # | Chapter | Covers |
|---|---|---|
| 1 | Rights you keep | exclusive vs non-exclusive, term & reversion, reading checklist |
| 2 | Copyright and ISBNs | registration (about $45–65), © page, free-vs-Bowker ISBNs ($0 vs about $125) |
| 3 | Wide distribution | KDP expanded vs IngramSpark, wholesale discounts (55% vs 40%), aggregators |
| 4 | Audiobook routes | ACX royalty share (0 upfront), PFH ($150–400/hr), self-recording, AI narration |
| 5 | Getting into libraries | OverDrive via D2D, Indie Author Project, Palace Marketplace, Ingram print |
| 6 | Direct sales | Payhip/Gumroad/Shopify fee math, 85–95% margins, print direct, consignment |
| 7 | Author taxes, plain numbers | 15.3% SE tax, bracket arithmetic at $5k–$50k, quarterly dues, deductible list |
| 8 | Putting it together | a week-by-week launch sequence, two worked scenarios, go-wide checklist |
| W1–W3 | Worksheets | rights map, six-question channel decision, one-page cost compare |

Companion projects for the numbers and files:

- **[kdp-profit-planner](https://github.com/dylanasdale)** — royalty math,
  printing costs, break-even units, price scans, monthly projections.
- **[kdp-interior-templates](https://github.com/dylanasdale)** — print-ready
  5x8 / 6x9 / 8.5x11 book interiors from HTML templates.

## Quick start

Requires Python 3.9+ (standard library only).

```bash
# Build the static site from docs/ into site/
python3 build.py

# Or build and verify every expected output exists
python3 build.py --check

# Then open the guide in any browser
```

The site lands in `site/` — start at `site/index.html`. Plain HTML, one CSS
file, no JavaScript, print-friendly.

Edit any `docs/*.md` file and re-run `python3 build.py` to regenerate.
Page order, titles, and the navigation live at the top of `build.py`.

## Run the tests

```bash
python3 -m pytest tests/ -v       # 52 tests: converter, site build, links
```

The suite covers the Markdown converter (headings, tables, wrapped bold,
checkboxes, code fences), internal-link validation (a broken `docs` link
fails the build), per-page credit/licence checks, and the end-to-end build.

## Layout

```
docs/                 the guide in Markdown (9 chapters + 3 worksheets)
site/                 generated static HTML (open index.html)
assets/base.css       the single stylesheet
build.py              the site builder (stdlib only)
tests/test_build.py   the test suite
LICENSE               MIT, Copyright (c) 2026 Asdale Dynamics, LLC
STATUS.md             what was built, how it was verified
```

## Notes on the numbers

Every fee, rate, and tax figure in the guide is a **round planning number**,
written to be realistic without pretending to be live data. Platform pricing
changes often; the guide says so wherever it matters, and each chapter
points at the platform's own pricing page as the final word. The tax chapter
is educational arithmetic (US federal, with an Indiana state footnote), not
advice.

## License

MIT — see `LICENSE`. Copyright (c) 2026 Asdale Dynamics, LLC.
