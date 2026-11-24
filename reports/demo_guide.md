# Five-minute interactive demonstration

The audience can predict a result, reveal the calculation, inspect a real object,
and change a culture-label assumption. The saved 3,000-object snapshot supports
the whole analysis without an Internet connection. One optional live API call
has an explicit success/failure state and never silently falls back to cache.

## Prepare

- Open the correct hosted deployment URL, or start `python -m streamlit run app.py`
  locally. Confirm the matching count is 2,990 with all explorer filters reset.
- Open **Live demo**. Its steps use the full saved sample independently of the
  explorer sidebar filters; this scope is labeled in the interface.
- Keep the source files and Q1/Q2/Q3 reports open for questions. No bulk acquisition
  is needed during the presentation.
- Rehearse the failure case: if the live request fails, say so and expand the
  clearly labeled saved processed metadata. It is not a fresh API response.

## 0:00–0:20 — Question and sample

> I use The Met's API to compare recorded dates, medium composition, and documented
> culture labels. I fixed 1,000 object IDs from each of three departments: 3,000
> records in total. Equal targets are my sampling design, not the museum's proportions.

## 0:20–1:10 — Click a fresh API request

In **Live demo → Live API**, choose a department and click **Fetch this object from
the API now**. The button refreshes exactly one sampled object-detail endpoint,
using a bounded timeout and no response cache. Expand the received JSON and show
the real response organized as a DataFrame.

Explain that the research script used `get_departments`, `get_object_ids`, and
`fetch_object` to acquire the complete sample and cache records as JSON Lines.
The classroom button refreshes one existing sampled ID and does not replace the
research sample. If it fails, show the saved-evidence expander and explain that
all analysis remains available offline. Do not wait through repeated retries.

## 1:10–2:10 — Audience prediction and NumPy reveal

Switch to **Predict and compare**. Ask:

> Which sampled department do you expect to have the earliest median recorded
> begin year?

Select the audience's prediction and click **Reveal the department comparison**.
The answer is computed from the saved data, not hard-coded. Explain the groupby
summary and median/quartiles; open **Show the NumPy calculation** briefly.
For the committed sample, Greek and Roman Art has the earliest median, 530 BCE.
These are date-interval lower bounds, not exact creation dates.

## 2:10–3:10 — Change the medium view

Click the sidebar **Painting media** preset and select **Q2 · Media**. Point to
century sample sizes and explain the within-department/century denominator.
The full sample has 24/25 tempera records in century 14 CE and 303/350 oil records
in century 19 CE. This describes sampled catalog composition, not a causal history
of worldwide artistic practice.

Optionally select `oil_painting` in the sidebar and switch to **Q1 · Dates** to
inspect that subset's date distribution. Reset **Medium group** to **All medium
groups** before interpreting full medium composition; otherwise shares are
conditional on the medium selection.

## 3:10–4:10 — Interactive culture calculator

Return to **Live demo → Culture calculator**. Select European Paintings to show
that no culture labels are documented: diversity is undefined, not zero. Then
select Asian Art and toggle the uncertain-attribution exclusion. The documented
count and NumPy indices update from actual labels.

Open **Show the probability and NumPy steps** to explain normalization,
`np.log`, row sums, Shannon entropy, and Gini-Simpson. These calculations do not
use an external diversity helper. Different catalog vocabularies prevent a direct
ranking of historical societies by these indices.

The calculator uses all sampled objects in its chosen department. The separate
**Q3 · Cultures** explorer tab follows date/medium filters and can have different
denominators. State which view is being shown.

## 4:10–4:40 — Let the audience pick an object

Use **Object browser**. Search a word from a visible title or artist, choose one
matching object, and inspect its metadata. The selector offers the first 100
matching IDs; search to narrow it. Examples are not claimed to be a representative
random subsample. Searches affect only the object browser, not Q1/Q2/Q3 statistics.

## 4:40–5:00 — Limitations

> Coverage varies by field, dates can be imprecise, and medium classes are coarse
> rules. I checked sensitivity to wide dates and uncertain labels. These are
> descriptive sample findings, not population claims. PyTorch is optional and not
> needed for these questions.

## Course requirement mapping

| Requirement | Demonstration evidence |
|---|---|
| Programmatic API acquisition | Fresh object-detail request with visible success/failure; three-stage research client available |
| DataFrame and processing | Live response DataFrame, processed metadata, date/medium/culture features and source functions |
| Meaningful pandas | Department grouping, medium crosstabs, filtered object rows, coverage tables |
| Meaningful NumPy | Computed medians/IQR, row-normalized proportions, Shannon/Gini-Simpson calculator |
| Questions/results | Prediction reveal and Q1/Q2/Q3 views with explicit populations |
| Interface/visualization | Tabs, presets, department/year/medium filters, charts, search and object selection |

If hosting is unavailable, the committed compact snapshot runs locally. Saved
API evidence must be labeled honestly. The formal final report and actual class
presentation are still separate deliverables.
