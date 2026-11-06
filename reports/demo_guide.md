# Five-minute demonstration guide

This is a rehearsal plan for the current checkpoint. Q1 is demonstrated end to
end and a minimal Streamlit application is available. Q2 descriptive results are now available; Q3 remains unfinished. Prepare the later
results before the final course demo rather than presenting them as completed.

## Prepare before class

1. Install dependencies and acquire the fixed sample using the root README.
2. Run the tests, rehearse the two commands below, and start the app on the presentation machine with `python -m streamlit run app.py --browser.gatherUsageStats=false`. Keep its browser tab open.
3. Open `process_data.py` at `build_dataframe` and `temporal_summary`.
4. Open the [Q1 figure](figures/q1_date_distribution.png) and the
   [result summary](full_sample_results.md) in separate tabs. Enlarge the figure
   before presenting. The PNG, summary, and aggregate CSVs are available on GitHub;
   the compact app snapshot is committed; the terminal snapshot/API analysis commands
   require the completed raw research cache if used on the presentation machine.
5. Use an activated Python environment. In the prepared cloud machine, replace
   `python` with `/workspace/met-venv/bin/python` if needed.

With the app already running, only two terminal commands are needed during the demonstration:

```bash
python api_demo.py --department 11
python demo_snapshot.py
```

The first makes real API requests. The second uses the completed, cached sample
and displays real DataFrame examples and numerical summaries without downloading
3,000 objects again. Do not present cached output as a live API call.

## 0:00-0:20 — Problem and sample

Say:

> My project explores temporal and cultural patterns in The Met's collection
> metadata. For this checkpoint, I sampled 1,000 objects from each of three
> departments. Today I will show how the data becomes a comparison of their
> recorded date ranges.

Mention that equal targets are a sampling choice, not the museum's actual
collection proportions.

## 0:20-1:10 — Live programmatic API acquisition

Run `python api_demo.py --department 11`.

Point out the department, candidate ID count, and returned object metadata. Say:

> Python first gets the departments, then the object IDs for one department,
> then a complete metadata record. The acquisition client adds a timeout,
> handles failures, and saves successful research records to a local cache.

A department can contain frames and other objects as well as paintings. Do not
promise the live example's title or candidate count will remain unchanged.

## 1:10-1:40 — pandas structure, cleaning, and aggregation

Run `python demo_snapshot.py` and show sections 1-3.

Explain:

> Each JSON record becomes one DataFrame row. I standardize blank strings as
> missing, preserve the original fields, and add date flags, a signed century,
> and a coarse medium category. The sample contains 3,000 records, but only
> 2,990 currently pass the date rules. I group by department to report the
> number available for the temporal question.

Point to these actual operations in `process_data.py` if asked:
`pd.DataFrame(records)`, `.replace(...)`, `df['century']`, and
`df.groupby('department')` in the demo helper. For field completeness, optionally
show the committed [missing-value table](results/field_completeness.csv).

## 1:40-2:20 — Meaningful NumPy computation

Show section 4 of the terminal output and `temporal_summary` in the source.
Explain these lines rather than reading the whole function:

```python
# Convert the eligible department years into a numerical vector.
years = group.loc[eligible.loc[group.index], 'begin_year'].to_numpy(dtype=float)
# Calculate the middle 50% boundaries and the median.
q1, q3 = np.percentile(years, [25, 75])
median = float(np.median(years))
# The interquartile range describes the central spread in the API year encoding.
iqr = q3 - q1
```

Say:

> These computations answer the project question: the median compares the
> central date, and the IQR compares the spread of the middle half of the
> records. NumPy is doing numerical analysis, not just storing an array.

Negative numbers denote BCE. These are recorded begin-year bounds, not exact
creation dates.

## 2:20-4:20 — Simple application, question, and findings

Switch to the already running Streamlit browser tab. Start with all departments
and the full year range. Select European Paintings and point out its 1,000 matching
records and median 1760. Narrow the year range and show that record counts,
statistics, charts, and object metadata update together. Optionally choose one
century to inspect the exploratory medium composition, and explain the Q2 small-group/date limitations. Keep the
full Q2 report available for questions. Reset the filters if returning to the full-sample statistics.

Then open the committed Q1 figure and ask:

> How do the temporal distributions differ across the three sampled departments?

Point to the median lines and the boxes. Report:

- Asian Art: median begin year 1700 CE; IQR 300 years.
- European Paintings: median begin year 1760 CE; IQR 240 years.
- Greek and Roman Art: median begin year 530 BCE; IQR 170 years.

Say:

> The classical department's sampled date bounds are much earlier. These are
> patterns in sampled catalog records, not a claim about the entire history of
> art. The plotted outliers are observations, not automatically data errors.

Briefly show the sensitivity table: excluding date intervals over 500 years
preserves the median ordering, but Asian Art's IQR becomes 200 years, below the
European Paintings IQR of 240. Therefore the spread comparison needs qualification.

## 4:20-5:00 — Limitations and next steps

Say:

> Ten zero-bound date records are held out of this temporal analysis. Date
> intervals can be imprecise, and some descriptive fields have uneven coverage.
> In particular, culture is entirely blank for European Paintings, while artist
> nationality is entirely blank for Greek and Roman Art. I will refine medium
> categories for the trend question and restrict cultural comparisons to fields
> with adequate documentation. The current application is a minimal explorer. I do not use
> PyTorch because this project does not need a machine-learning component.

The Q2 report provides descriptive results; do not imply that Q3 is complete. The explorer
provides the simple application layer; further features should serve the
remaining research questions rather than expand the frontend unnecessarily.

## If the live API fails

Explain the observed error and show the client code, request logs, and previously
acquired real records. Explicitly label them as saved evidence. Move on to the
cached analysis rather than waiting through a bulk acquisition. Saved evidence
is a contingency, not proof that a fresh live request succeeded.

## Questions to rehearse

- Why three departments and equal sample sizes? Comparison within a documented
  stratified sample; this is not a collection-wide proportion estimate.
- How is the sample reproducible? Seed plus the exact committed ID manifest.
- How are missing values handled? Per question, without deleting every record
  that lacks an unrelated field.
- Why not count year zero as a century? Conventional BCE/CE centuries have no
  ordinary year zero; API zero bounds are separately reviewed.
- Why NumPy? It directly computes medians, percentiles, IQRs, and vectorized
  transformations that support the temporal question.
- Why medians and quartiles? They describe the center and central spread while
  remaining informative in long-tailed distributions; uncertain dates still need
  a separate sensitivity analysis.
- What is unfinished? The refined Q3, further validation where appropriate, and the final course report. The interface and descriptive Q2 analysis are implemented.
