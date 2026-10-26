# Reading digest: molecular CSP + AI-for-science landmarks

A daily brief built on one rule: **reading 100 new but unimportant papers is no
better than reading one really important one.** Every candidate is judged on
three questions, most are skipped, an empty day is a valid day, and every day
also offers one established landmark paper worth 30 minutes.

## What it does

Two lanes feed one strict gate:

- **Molecular CSP (SOTA).** New crystal structure prediction work from OpenAlex
  (published + ChemRxiv), Crossref (CI fallback) and arXiv, regex-gated to the
  molecular field as before.
- **AI for Science (broad).** Machine-learning papers in high-visibility science
  venues (Nature, Science, Nature Machine Intelligence, Nature Computational
  Science, Nature Chemistry, Nature Materials, PNAS, Science Advances, JACS) and
  ML x science arXiv categories. Deliberately broad: the judge, not the query,
  decides.

**The judge (`judge.py`)** answers, for every candidate, the reader's three
questions on a 1-5 scale:

1. **Worth 30 minutes?** Is it novel, important, breakthrough-level and high
   quality enough to spend 30 minutes on?
2. **Inspiring?** Insightful or inspiring for the reader's own work (molecular
   CSP with genetic algorithms), or for AI-for-science research in general?
3. **Foundational?** Does it contain foundational knowledge or theory worth
   reading and learning?

A cheap triage model (Haiku) first drops obvious noise (experimental-only,
off-topic, tooling, incremental ML-potential tweaks); a frontier model (Opus)
then scores the survivors with structured output. The verdict is derived in
code: **read** needs Q1 >= 4 and (Q2 >= 3 or Q3 >= 4); **skim** is Q1 >= 3 with
some Q2/Q3 signal; everything else is **skip** and never published. Flags for
likely low-quality or machine-generated abstracts force a skip. Every decision
is cached in `site/data/judged.json`, so a paper is judged exactly once.

**Landmark of the day (`landmarks.py`)** ignores dates on purpose. Two pools
alternate day by day: a curated canon of AI-for-science breakthroughs and the
theory behind them (AlphaFold, flow matching, diffusion models, Boltzmann
generators, GNoME/MatterGen, AlphaGo-style search, evolutionary-computation
theory, ...) and the well-cited molecular-CSP classics mined by `classic.py`.
Seeds are only identifiers; `landmarks.py refresh` resolves each through
OpenAlex and keeps it only if the resolved title matches, so every record the
reader sees is real. The daily pick is explained through the same three
questions plus a 30-minute reading guide; "none of these is worth it" is an
allowed answer.

Outputs (one run):

- **`site/`** - the **Reading Room** website: Today (what's worth reading,
  landmark of the day, top picks / more worth reading / set aside), This Week,
  **Landmarks** (your accumulating canon), History, Starred (+ Zotero export).
- `csp_digest.html` - the styled single-day brief (standalone).
- `obsidian_notes/`, `csp_digest.ris` - only **read**-verdict papers, with the
  three scores in the frontmatter.
- `csp_digest.json` - machine-readable dump of everything kept (read + skim).

Everything is standard-library Python; no `pip install`.

## Run locally

```bash
export OPENALEX_API_KEY=...      # free account key: https://openalex.org/settings/api
export ANTHROPIC_API_KEY=...     # required for judging and the landmark pick
python3 digest.py                # writes csp_digest.html + site/data/<today>.json
```

Validate the model calls before enabling anything in CI:

```bash
python3 judge.py --selftest                                  # one live call per stage
python3 judge.py --file digests/csp_digest_2026-10-26.json   # re-judge an old day, see the scores
python3 landmarks.py pick --lane ai4sci                      # preview a landmark (no ledger write)
python3 test_judge.py && python3 test_landmarks.py           # offline tests
```

Tunables (environment variables):

| var | default | meaning |
|---|---|---|
| `DIGEST_DAYS` | `2` (CI: `14`) | look-back window in days |
| `DIGEST_SCOPE` | `molecular` | `molecular`, `inorganic`, or `both` for the CSP lane |
| `JUDGE_MODEL` | `claude-opus-5-5` | scores the three questions |
| `JUDGE_EFFORT` | `medium` | `low` .. `max` thinking effort for the judge |
| `TRIAGE_MODEL` | `claude-haiku-5-5` | cheap pre-filter; set to `""` to skip triage |
| `JUDGE_READ_Q1/Q2/Q3` | `4` / `3` / `4` | read thresholds (no re-judging needed) |
| `JUDGE_REQUIRED` | unset (CI: `1`) | refuse to publish when the judge could not run |
| `DIGEST_JUDGE` | `1` | `0` publishes everything unjudged (local debugging) |
| `LANDMARK_OF_DAY` | unset (CI: `1`) | pick one canon paper per day |
| `LANDMARK_LANE` | `alternate` | `ai4sci`, `mcsp`, or alternate by day |
| `EXPORT_OBSIDIAN` / `EXPORT_ZOTERO` | `1` | set `0` to skip those exports |

Cost: a paper is judged once (cached). After the first run, expect a few dozen
Haiku triage calls and roughly 10-20 Opus judgments per day, plus one landmark
pick and one synthesis call.

## Run daily on GitHub Actions

1. Repository secrets: `OPENALEX_API_KEY`, `ANTHROPIC_API_KEY` (required).
2. `.github/workflows/daily.yml` runs daily, commits `csp_digest.*`,
   `obsidian_notes/`, `digests/` and `site/data/` (including the judge cache
   and the landmark ledger) back to the repo, and deploys `site/` to GitHub
   Pages (**Settings -> Pages -> Source: GitHub Actions**).
3. A run where the judge cannot do its job exits non-zero instead of
   publishing unjudged papers.

## Retuning

- **What counts as "worth reading"**: the reader profile and the three
  questions are the `READER` / `RUBRIC_PROMPT` strings at the top of
  `judge.py`. Bump `PROMPT_VERSION` after editing them so cached verdicts are
  recomputed. Thresholds are env vars (table above).
- **Where to look**: `QUERIES_MOLECULAR` / `ARXIV_QUERIES` (CSP lane),
  `AI4SCI_JOURNALS` / `ARXIV_QUERIES_AI4SCI` (AI4Sci lane) in `digest.py`.
- **The canon**: add identifiers to `SEEDS` in `landmarks.py` and run
  `python3 landmarks.py refresh` (needs `OPENALEX_API_KEY`); commit
  `review/landmarks_pool.json`. Unresolved seeds are listed in that file and
  never shown. The MCSP classics pool is `review/classics_pool.json`
  (`python3 classic.py` refreshes it).

## Notes

- Every link is built from the identifier the API returns; DOIs and arXiv IDs
  are never hand-typed into output.
- Fetched titles/abstracts are treated as data, not instructions.
- Scores, contribution lines and landmark explanations are model-generated from
  titles and abstracts; they decide reading order, not facts.
- No API keys are written to disk or committed.
