# CSP literature digest

A daily brief of new **molecular crystal structure prediction** papers, pulled
from OpenAlex (published articles + ChemRxiv preprints) and arXiv. Filters
off-field noise, deduplicates, scores each paper on two axes, tags it with
field-locating keywords, tags watchlist authors, and (optionally) adds a
one-line AI "why it matters".

Each paper carries:
- **relevance (0–100)** — how central it is to molecular CSP (query breadth,
  explicit "crystal structure prediction", GA/molecular vocabulary, topical density).
- **significance (0–100)** — a *prior* on importance from field-normalized
  citation impact (FWCI), log citations, watchlist authorship, and venue.
  New preprints legitimately score low here until they accrue signal.
- **keyword tags** — e.g. `genetic-algorithm`, `generative-model`,
  `ML-potential`, `free-energy`, `polymorphism`, `cocrystal-salt` — to place
  the work in the subfield at a glance.

Outputs (one run):
- **`site/`** — a browsable **website** (see below). Each run appends
  `site/data/<date>.json` and updates `site/data/index.json`; the history
  accumulates in the repo over time.
- `csp_digest.html` — the styled single-day brief (standalone).
- `obsidian_notes/` — one Markdown note per paper (YAML frontmatter with
  tags/scores/DOI, `[[wikilinks]]` for authors + field tags, an empty "My notes"
  section) plus a dated index note. Drop into an Obsidian vault.
- `csp_digest.ris` — Zotero import file (File → Import).
- `csp_digest.json` — machine-readable dump for any downstream knowledge base.

## The website (GitHub Pages)

`site/index.html` is a self-contained single-page app (no build step, no
server, no dependencies) that reads the accumulated `site/data/*.json`:

- **Today** — new papers with a one-sentence **Contribution** line, scores,
  tags, expandable abstract, and a "what's new today" synthesis. An unread
  badge counts papers you haven't opened.
- **This Week** — the top papers of any 7-day window by relevance+significance,
  deduplicated across daily runs. Scroll back week by week.
- **History** — every archived day, browsable.
- **★ Starred** — click ☆ on any paper to save it (stored in your browser,
  private to you). One-click **export starred → Zotero RIS**.
- A **reading streak** counter and starred count encourage daily visits.

Starring and read-state live in your browser's `localStorage` — no login, no
backend, per-device. The daily job only ever *adds* data; it never touches
your stars.

`digest.py` uses only the Python standard library — no `pip install` needed.

## Run locally

```bash
export OPENALEX_API_KEY=your_openalex_key      # free from https://openalex.org
export ANTHROPIC_API_KEY=your_anthropic_key    # optional: enables summaries
export OPENALEX_MAILTO=you@example.org         # optional: polite-pool contact
python3 digest.py                              # writes csp_digest.html
```

Tunables (environment variables):

| var             | default                    | meaning                              |
|-----------------|----------------------------|--------------------------------------|
| `DIGEST_DAYS`     | `2`                        | look-back window in days                       |
| `DIGEST_SCOPE`    | `molecular`                | `molecular` (default), `inorganic`, or `both`. In `molecular` mode an inorganic-exclusion gate drops alloy / oxide / high-pressure-phase hits (incl. those arriving via arXiv) unless a molecular-crystal signal is present. |
| `SUMMARY_MODEL`   | `claude-3-5-haiku-latest`  | Anthropic model for summaries                  |
| `EXPORT_OBSIDIAN` | `1`                        | set `0` to skip the `obsidian_notes/` folder   |
| `EXPORT_ZOTERO`   | `1`                        | set `0` to skip the `csp_digest.ris` file      |

## Run daily on GitHub Actions

1. Create a new GitHub repo and push these files.
2. **Settings -> Secrets and variables -> Actions -> New repository secret**, add:
   - `OPENALEX_API_KEY` (required)
   - `ANTHROPIC_API_KEY` (optional — omit to skip AI summaries)
   - `OPENALEX_MAILTO` (optional)
3. The workflow in `.github/workflows/daily.yml` runs at **07:00 UTC every
   weekday** and commits `csp_digest.html` (plus a dated copy under `digests/`)
   back to the repo. It also uploads the HTML as a downloadable workflow
   artifact.
4. Trigger a test run any time from the **Actions** tab -> *CSP daily digest*
   -> **Run workflow** (you can override the window and scope there).

Change the schedule by editing the `cron:` line (times are UTC).

### Enable the website

1. **Settings -> Pages -> Build and deployment -> Source: GitHub Actions.**
2. Run the workflow once (Actions tab). The `deploy` job publishes `site/` to
   `https://<you>.github.io/<repo>/`.
3. Bookmark that URL. Each weekday run appends a new day and redeploys; your
   stars and reading streak persist in the browser.

The workflow needs `pages: write` and `id-token: write` permissions (already
set in `daily.yml`). No extra secret is required for Pages.

## Retuning what it tracks

Edit the lists at the top of `digest.py`:

- `QUERIES_MOLECULAR` / `QUERIES_INORGANIC` — the topic searches.
- `WATCHLIST` — authors to flag. Tagging is by surname **on papers the topic
  search already found**, so a common name only tags when its paper is already
  CSP-relevant.
- `POS_PAT` / `CSP_PAT` / `NEG_PAT` — the relevance gate. arXiv results are
  trusted via query targeting and not gated.

## Notes

- Every link is built from the identifier the API returns; DOIs and arXiv IDs
  are never hand-typed.
- Fetched titles/abstracts are treated as data, not instructions.
- No API keys are written to disk or committed; they are read from the
  environment (GitHub Actions injects them from repository secrets).
