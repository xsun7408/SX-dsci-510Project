# Fifteen-minute project presentation

**Confirmed format: 15 minutes total, including questions.** Plan 13 minutes of
presentation and live interaction, then reserve 2 minutes for questions or recovery.
The course document lists the required evidence; the 15-minute limit comes from
the student's presentation instructions. This guide is a rehearsal plan, not a
claim that the actual class presentation has been completed.

Use this as the main guide. A historical five-minute fallback is preserved in the local learning backup
if the instructor shortens the slot; it is not the current presentation plan.

## Run of show

| Time | Duration | Show / operate | Purpose |
|---|---:|---|---|
| 0:00–1:00 | 1:00 | Title, motivation, three questions | Establish why the data and analyses matter |
| 1:00–3:00 | 2:00 | Acquisition pipeline + Live demo → Live API | Prove programmatic acquisition and distinguish live from cached data |
| 3:00–5:00 | 2:00 | DataFrame, missing-value table, cleaning examples | Explain meaningful pandas processing and aggregation |
| 5:00–7:00 | 2:00 | Actual NumPy probability/diversity code | Explain one computation, its input/output, and its purpose |
| 7:00–8:30 | 1:30 | Predict and compare → reveal Q1 | Audience interaction plus temporal finding and limitations |
| 8:30–10:00 | 1:30 | Painting media preset → Q2 tab | Explain within-century proportions and one concrete contrast |
| 10:00–11:30 | 1:30 | Culture calculator / Q3 tab | Show coverage-aware interpretation and uncertainty toggle |
| 11:30–12:15 | 0:45 | Object browser → search and select | Demonstrate useful filtered application behavior |
| 12:15–13:00 | 0:45 | Limitations, conclusion, next steps | State what the results support and what remains |
| 13:00–15:00 | 2:00 | Questions / recovery margin | Answer with code, figures, and evidence already open |

**Hard stop:** stop the main presentation at 13:00. Ask for one quick audience
prediction, not a long discussion. Count interaction and loading time inside each
section. If a live call fails, move to the labeled saved evidence immediately.

## Prepare the screen, files, and slides

Use about **8 concise slides**, plus the live app and two code excerpts:

1. Title, motivation, and Q1/Q2/Q3.
2. Data source, API pipeline, and fixed sampling design.
3. DataFrame structure, field coverage, and cleaning rules.
4. Meaningful NumPy: probabilities, Shannon, and Gini-Simpson.
5. Q1 result and begin-year limitation.
6. Q2 result and denominator/sample-size limitation.
7. Revised Q3, coverage, and label-granularity limitation.
8. Conclusions, limitations, and reproducibility.

This is a slide outline; no slide-deck file is implied. The existing application
covers live interactions. Keep text short and refer to the [speaker script](presentation_script.md)
for spoken explanations instead of putting full paragraphs on slides.

Before the timer starts:

- Open the correct hosted URL: https://xsun7408-sx-dsci-510project-app-kwdahk.streamlit.app/
- Keep a local snapshot-based app ready if hosting is unavailable. Confirm 2,990
  matching rows with all explorer filters reset. A local test does not prove the
  public website's current health.
- Open `acquire.py`, `process_data.py`, `analyze_cultures.py`, and these three reports:
  [Q1](full_sample_results.md), [Q2](q2_results.md), [Q3](q3_results.md).
- Keep the [completeness CSV](results/field_completeness.csv) and
  [Q3 coverage table](results/q3_department_summary.csv) available.
- Disable unrelated notifications and enlarge the browser/code font for the room.
- Rehearse the network-failure path once. Never present saved evidence as a fresh
  successful API response, and never acquire 3,000 objects during the presentation.

## 0:00–1:00 — Motivation and questions

Explain the user-facing goal: compare the sampled departments by recorded dates,
medium composition, and documented culture labels. State the three questions in
plain language. Mention that the project is individual and one substantive API
source meets the source-count requirement. Do not spend this minute listing libraries.

## 1:00–3:00 — Source, sample, and a live request

Show the pipeline:

`departments → candidate object IDs → fixed sampled IDs → object JSON → JSON Lines cache`

Name `get_departments`, `get_object_ids`, and `fetch_object` in `acquire.py`. Explain
that seed 510 and the actual ID manifest fix 1,000 IDs per department, 3,000 in
total. Equal targets are not the collection's natural department proportions.
The source is https://metmuseum.github.io/; the recorded acquisition was on
November 5, 2026 in America/Los_Angeles, with exact UTC time in the manifest.
The API needs no key; the documented limit is 80 requests/second, while the
research run used roughly one request/second.

In **Live demo → Live API**, choose one department and click **Fetch this object
from the API now**. Show the fresh-success state, actual JSON, and response
DataFrame. The button refreshes one sampled object-detail endpoint; it does not
repeat all three acquisition stages or replace the research dataset. Explain
JSON Lines caching, skipping cached IDs, timeouts, backoff, and stopping after
repeated 403s. A single demo refresh uses a bounded request without retries.

If it fails: say "This fresh request failed; I will show previously acquired
real evidence and continue with the cached analysis." Expand the labeled saved
metadata, point to the acquisition code, and continue. This is a fallback, not
proof of successful live acquisition.

## 3:00–5:00 — pandas: structure, quality, and analysis

Show the DataFrame and actual transformations, not just `head()`:

- `pd.DataFrame(records)`: one sampled object per row.
- `.replace(r'^\s*$', pd.NA, regex=True)`: normalize blank strings.
- Date flags: zero-bound, missing/nonfinite/noninteger, reversed, and wide ranges.
- Derived `century` and `medium_category`; original fields retained.
- `groupby('department')`: group sizes and summaries.
- `pd.crosstab([department, century], medium_category)`: counts feeding Q2.

Point out actual coverage: culture is 100% recorded for Asian Art, 96% for Greek
and Roman Art, and 0% for European Paintings. Artist nationality has a different
coverage pattern. Missing nationality does not disqualify a record from a date
analysis. There are 3,000 sampled records but 2,990 usable under the current date
rules. Conventional centuries have no ordinary year zero; keep ambiguous dates
for review. Century uses the interval start, not an exact creation date.

Optional terminal aid, already prepared before class:

```bash
python demo_snapshot.py
```

This command needs the research cache and makes no live API call. On a machine
without the raw cache, use the app, committed summaries, and source excerpts.

## 5:00–7:00 — NumPy: explain purpose and mechanics

Use `analyze_cultures.py` → `diversity_from_counts`. Explain one vectorized method
in depth, then briefly mention medians/IQR and Q2 broadcasting as additional uses.

1. Counts are real documented-label frequencies for each group.
2. Row sums with `axis=1, keepdims=True` preserve a broadcastable column dimension.
3. Divide counts by their row totals to obtain probabilities.
4. Compute `H = -sum(p * ln(p))` and `1 - sum(p**2)` using NumPy operations.
5. Zero probabilities contribute zero without evaluating `ln(0)`.
6. An all-missing row returns undefined indices. A genuinely single-label group
   has H=0; these situations must not be confused.

Explain why this is meaningful: it quantifies concentration among documented
labels and helps answer revised Q3. Turning a list into an array alone would not
answer that question. Do not imply that z-score standardization is required;
it was not added without an analytical purpose.

Keep the Q1 numeric answer hidden until the audience prediction in the next step.

## 7:00–8:30 — Q1: predict and reveal

Open **Live demo → Predict and compare**. Give the audience about 10 seconds to
predict the earliest median department, select their choice, then reveal.
The result is computed from the saved sample. In this dataset, medians of
recorded begin years are Asian Art 1700 CE, European Paintings 1760 CE, and
Greek and Roman Art 530 BCE. Explain the median and IQR, not every table cell.

Show the broad date distribution or Q1 figure. State that wide date intervals
change spread comparisons: Asian Art's IQR falls from 300 to 200 years after
excluding spans over 500 years, versus 240 years for European Paintings.
Do not interpret all plotted outliers as errors.

## 8:30–10:00 — Q2: inspect medium composition

Click **Painting media**, select **Q2 · Media**, and keep **All medium groups**.
Explain the within-department/century denominator and the n >= 20 display rule.
Small groups remain in the exports; they are not zero-record periods.

Use one clear result: European Paintings has 24/25 tempera records in recorded
century 14 CE (96.0%) and 303/350 oil records in 19 CE (86.6%). These are sampled
catalog composition differences, not a causal or worldwide history of art.

If time permits, briefly choose `oil_painting` and look at Q1, then reset it.
A medium-filtered chart cannot be interpreted as the full medium mix. State that
keyword rules preserve raw text and use documented precedence for composite media.

## 10:00–11:30 — Q3: show missingness before indices

Use **Live demo → Culture calculator**. Select European Paintings: no culture
labels are documented, so indices are undefined. Then select Asian Art and toggle
uncertain-attribution exclusion. Show how documented counts and indices update.

In the whole-department report, Japan/China total 81.5% of 1,000 documented Asian
Art records. Greek, Attic/Roman total 66.5% of 960 documented Greek and Roman Art
records. These are exact catalog labels, not interchangeable countries or artist
nationalities. Do not rank historical societies using the indices.

The guided calculator uses all sampled records. **Q3 · Cultures** follows explorer
date/medium filters and may have a different denominator (e.g. 991 Asian Art rows).
For century interpretation, show documented n >= 20 and coverage >= 80%; all 80
observed groups remain exported and 16 meet the primary Q3 rules.

## 11:30–12:15 — Audience-selected object

Open **Object browser**, search a word visible in a title/artist, and choose a
matching object. Show that metadata changes with the selection. The first 100
matching IDs are available in the selector; search narrows them. Example objects
are not claimed to be a representative random sample. Object search affects
only browsing, not the Q1/Q2/Q3 statistics.

## 12:15–13:00 — Limitations and close

State four limitations: stratified sampling, imprecise date bounds, coarse medium
rules, and uneven/unequally granular culture labels. Mention wide-date and uncertain-
attribution sensitivity checks. Summarize what the program contributes: a reproducible
acquisition-to-analysis workflow with useful, data-driven interaction. PyTorch is
optional and was not used. Stop the planned content at 13:00.

## 13:00–15:00 — Questions or recovery

Keep answers short; open the relevant code/table instead of improvising new claims.
If questions are sparse, use one evidence-based follow-up: "What changes when I
exclude uncertain culture labels?" Do not start an untested new feature.

| Likely question | Answer anchor |
|---|---|
| Why 3,000? | Focused individual-project target; 1,000 per department; not a course minimum |
| How is it reproducible? | Seed + actual sampled IDs + cached responses; future API metadata can change |
| Why separate missingness by question? | Unrelated missing fields do not invalidate otherwise usable observations |
| Why no country-based Q3? | Country is entirely missing in this sample; use culture labels with coverage |
| H=0 versus missing? | Single observed label versus undefined distribution with no documented labels |
| Why no z-score/model? | Existing calculations serve the questions; neither z-score nor PyTorch is mandatory |
| Does higher H mean a more diverse society? | No; vocabulary, granularity, documentation, and sample size differ |
| Can you claim museum-wide shares? | No; department targets were fixed by the sampling design |

## Coverage checklist

API acquisition, DataFrame processing, meaningful pandas, meaningful NumPy,
research questions/results, visualization/application, and whole-project questions
are all assigned explicit time. The actual class demo and final report submission
remain the student's deliverables.
