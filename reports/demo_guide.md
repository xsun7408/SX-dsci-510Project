# Five-minute demonstration guide

All three questions now have descriptive results. The app is implemented and
locally tested; the hosted installation must still be confirmed. This guide is
a rehearsal plan, not evidence that the actual class demo has occurred.

## Prepare before class

1. Test the hosted URL on the presentation machine. If hosting remains unavailable,
   run `python -m streamlit run app.py` locally using the committed compact snapshot.
2. For the live/cached terminal demonstrations, install requirements and retain the
   completed raw sample. `python api_demo.py --department 11` needs API connectivity;
   `python demo_snapshot.py` needs the research cache. Do not reacquire 3,000 objects
   during the presentation.
3. Open the app, `process_data.py` at `temporal_summary`, `analyze_cultures.py` at
   `diversity_from_counts`, and the [result overview](full_sample_results.md).
4. Keep [Q2](q2_results.md) and [Q3](q3_results.md) available for follow-up questions.
5. Rehearse once without network access: saved evidence must be explicitly labeled
   as previously acquired data, never presented as a successful live API call.

## 0:00–0:20 — Question and sample

> I use The Met's public API to compare recorded dates, medium composition, and
> documented culture labels. The fixed sample has 1,000 objects from each of three
> departments. Equal targets are my sampling design, not the museum's proportions.

## 0:20–1:00 — Live API acquisition

```bash
python api_demo.py --department 11
```

Point to the department, candidate IDs, and one actual metadata response. Explain
that Python requests the IDs before object details, with timeouts and failure
handling. The full acquisition saves successful responses in JSON Lines and skips
already cached IDs on restart. A department can include frames or other object
types, so avoid calling every returned object a painting.

## 1:00–1:40 — pandas processing and analysis

```bash
python demo_snapshot.py
```

Show the DataFrame shape, raw-to-derived fields, and department group counts.
Explain blank-to-missing normalization, date flags, century, medium categories,
and the difference between 3,000 sampled records and 2,990 eligible date records.
Point to groupby/crosstab and explain why every question has its own denominator.

## 1:40–2:20 — Meaningful NumPy

Explain either the Q1 median/quartiles or the Q3 diversity calculation in detail;
keep the other ready for questions. Do not try to read both full functions aloud.

> NumPy computes medians and percentiles to compare the center and spread of the
> recorded dates. For Q3, it converts category counts to probabilities, then uses
> vectorized log, multiplication, and reductions for Shannon entropy. Missing labels
> are excluded with coverage reported; an empty group is undefined, not zero diversity.

The Shannon formula is `-sum(p * ln(p))`; the implementation avoids log(0). These
are actual numerical calculations, not just conversion of a list to an array.

## 2:20–4:20 — App and three findings

Use around 40 seconds per question. The app's values change with filters, so quote
what is currently visible rather than reading whole-sample numbers into a subset.

- **Q1:** Select European Paintings with the full year range: 1,000 records and
  median begin year 1760. Point to the distribution. The full report compares
  this with Asian Art (1700) and Greek and Roman Art (530 BCE). Date bounds are
  not exact creation dates.
- **Q2:** Show European Paintings' century composition. In the full sample,
  tempera accounts for 24/25 records in recorded century 14 CE; oil painting
  accounts for 303/350 in 19 CE. These are catalog sample composition differences,
  not a causal history of all artistic practice. Sparse groups are flagged.
- **Q3:** Show that European Paintings has no documented culture labels and hence
  undefined indices. Switch to Asian Art to show its documented-label bars and
  coverage-aware entropy. The whole-department report has Japan/China totaling
  81.5% of 1,000 records; the app uses date-filtered records and can differ. Do not
  substitute artist nationality or rank historical societies by the indices.

Briefly move the year slider once to demonstrate that statistics, charts, and
object metadata come from the same filtered data. Do not spend time customizing
colors or browsing many object rows.

## 4:20–5:00 — Limitations and interpretation

> The sample is stratified by department. Catalog fields have uneven coverage,
> date intervals can be imprecise, and keyword medium groups are coarse. I checked
> sensitivity to wide date ranges and uncertain culture labels. The results describe
> these sampled metadata records, not worldwide art history or societal diversity.

PyTorch is optional and not used. Final report assembly and the actual presentation
remain separate deliverables.

## Questions to rehearse

- Why equal samples? A documented department comparison, not a population proportion.
- How reproducible? Seed plus the actual committed ID list; cached records preserve
  this acquisition, while future API metadata can change.
- Why exclude year-zero bounds? Conventional BCE/CE centuries do not have an ordinary
  year zero; ambiguous API boundaries are separately reviewed.
- Why two kinds of Q3 denominators? Department coverage includes all sampled objects;
  a century analysis requires usable dates. Missing cultures are not counted as a label.
- What does H=0 mean? One observed category. All labels missing is undefined instead.
- Can indices compare societies? No: exact labels differ in granularity, sample size,
  and catalog practice. They summarize the documented sample vocabulary.
- What if the API fails live? Explain the error, show the code and saved evidence,
  label it honestly, and continue with cached analysis rather than bulk downloading.
