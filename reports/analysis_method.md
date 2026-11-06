# Acquisition and temporal analysis methods

## Sample design

The recorded sample contains 3,000 API metadata records: 1,000 each from European
Paintings, Asian Art, and Greek and Roman Art. Sampling uses seed 510 and saves
the actual selected IDs. The pilot and full sample have separate manifests; the
shared cache is not itself the analysis population. The committed
[full manifest](../sampling/sample_3000_510.json) fixes the original sample.

Candidate IDs come from `/objects?departmentIds=...`; full records come from
`/objects/{objectID}`. Official documentation at https://metmuseum.github.io/
states that no API key is required and requests should be limited to 80 per
second. The full run used an approximately one-second request interval and
immediately appended successes to JSON Lines. HTTP 429 and selected temporary
failures receive bounded backoff; three consecutive 403 responses stop a run.
Failed IDs are not replaced.

The 3,000-record target is a project design choice, not a course minimum.
Equal targets support departmental sample comparisons, not inference about each
department's share of the entire collection. Departments can contain different
object types, including frames, and are not equivalent to one medium or genre.
No `isPublicDomain` restriction is applied to metadata. Image use requires a
separate permissions check; this checkpoint acquired no images.

## Date rules

- Convert empty and whitespace-only strings to missing values.
- Preserve the raw JSON. Keep sampled records and original date descriptions in
  the cleaned table, regardless of their eligibility for a particular question.
- Flag begin=end=0 with no `objectDate` description as likely unknown.
- Set aside any zero-bound interval for review rather than assigning year zero
  to a normal century.
- Exclude missing, nonfinite, noninteger, reversed, and zero-bound date intervals
  from Q1 start-year statistics.
- Flag spans over 500 years. Retain them in the primary Q1 summary, then compute
  a separate summary excluding them to assess sensitivity.
- Derive signed centuries from begin years: 1..100 maps to 1; -100..-1 maps to -1.
- Begin year is an interval lower bound, not necessarily an exact creation date.
  Objects spanning centuries may be assigned earlier than their actual creation
  century. Numeric year differences and summaries describe the API year encoding,
  not exact historical durations across the BCE/CE boundary.

## Medium rules

Ordered keyword matching assigns mutually exclusive coarse categories. For
example, `Oil on copper` first matches `oil_painting`, and `Terracotta` matches
`ceramic`. Unmatched strings become `other`, missing values become `unknown`,
and the original `medium` remains available for review. These categories are an
exploratory grouping, not a detailed museum materials ontology. Composite media
and uncovered strings require review before interpreting Q2.

## pandas and NumPy

pandas structures the DataFrame, normalizes missing strings, filters records,
creates features, groups departments, and exports tables. NumPy performs
vectorized century calculations and computes departmental medians, 25th/75th
percentiles, and IQRs for eligible start years. Q1 compares the original year
encoding; z-scores are not used to adjust sampling proportions.

## Reproduction

Follow the root [README](../README.md) to install dependencies and restore the
fixed manifest into `data/`. Then run:

```bash
python acquire.py --count 3000 --interval 1
python inspect_quality.py data/sample_3000_510.json
python process_data.py data/sample_3000_510.json --output-dir data/processed_3000
python -m unittest discover -s tests -v
```

The processing script rejects incomplete samples. Results must be calculated
from acquired records, not hard-coded findings. Committed tables and the PNG
are a checkpoint snapshot; regenerated outputs remain under ignored `data/`.

## Reviewed medium classification (version 2) and Q2

Version 2 prioritizes ceramic descriptions over decorative enamel wording, and
ink/watercolor/print techniques over textile support. It adds explicit groups for
other drawing/painting media, enamel, lacquer, ivory/bone/horn, clay/earth, and
paper/parchment, plus reviewed mineral and wood terms. For example, ink on silk
is an ink-work category, porcelain with enamels remains ceramic, and unfired clay
is not forced into a fired-ceramic category. These remain coarse ordered
conventions for mixed media, not definitive museum taxonomy.

Q2 uses pandas crosstab counts and NumPy row sums with `keepdims=True` to compute
within-department/century shares through broadcasting. Other/unknown records stay
in denominators. All observed groups are saved; the main chart uses n >= 20. The
wide-date check records both percentage changes and loss of qualifying groups,
so a vanished or newly sparse century is not silently omitted from limitations.
