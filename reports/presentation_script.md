# Reference speaker script: 15-minute slot including questions

Plan: 13 minutes of explanation and interaction, then 2 minutes for questions.
Bracketed directions are actions, not words to read aloud. This is an English
reference script, not a required verbatim text. Rehearse at your natural pace;
allow clicks and the audience prediction to consume time. Stop the main content
at 13:00 even if an optional detail must be skipped.

## 0:00–1:00 — Introduction

My project explores The Met's collection through its public API. I wanted to
understand how the recorded dates, materials, and culture labels differ across
museum departments, and to build a small explorer that lets users inspect the
evidence themselves.

I focus on three questions. First, how do the departments differ in their
recorded date distributions? Second, how does medium composition vary across
recorded centuries? Third, which culture labels are documented, and how
concentrated are those labels? The last question was refined after checking
missing values. My final sample has 3,000 objects: 1,000 from each department.

## 1:00–3:00 — API acquisition

[Show the source and acquisition pipeline; open Live demo → Live API.]

The source is The Metropolitan Museum of Art Collection API. My Python program
first gets department IDs and names, then candidate object IDs for each department,
and finally detailed object records. These stages are separate functions:
get_departments, get_object_ids, and fetch_object.

I used a fixed random seed and saved the actual sampled ID list. The seed alone
would not fully protect reproducibility if the API's candidate list changed.
Every successful record was saved to a JSON Lines cache, so interrupted runs
could resume without downloading existing records again. Requests have timeouts,
logging, and bounded retry rules. Repeated access denials stop the bulk run.

[Click the request button once; show the JSON and DataFrame.]

This button makes one fresh object-detail request. It does not download the
whole dataset again or change the research sample. The full cached analysis
remains usable if the network fails. If this request fails, I will label the
saved metadata as offline evidence rather than present it as a live response.

## 3:00–5:00 — DataFrame, missingness, and pandas

[Show the DataFrame, missing-value table, and short cleaning/grouping excerpts.]

Each object becomes a DataFrame row. I standardize empty strings as missing
values, preserve the original metadata, and add date flags, a century column,
and a coarse medium category. The sample has 3,000 records, but only 2,990 pass
the date rules used in the temporal analysis. Zero-bound dates are held for
review instead of being assigned to an ordinary year zero.

Missingness changed the third question. Culture is documented for all Asian Art
records, 96 percent of Greek and Roman Art records, and none of the European
Paintings records. Artist nationality has a different coverage pattern, so I do
not substitute it into the culture field. A missing nationality also does not
make an otherwise usable date record invalid.

The pandas work includes filtering, derived columns, groupby summaries, and
crosstabs. For example, the medium count table groups by both department and
century. Those operations connect the raw records to the questions; this is
more than displaying the first few rows.

## 5:00–7:00 — Meaningful NumPy

[Open diversity_from_counts; point to the count matrix, row sums, and log/reduction.]

One meaningful NumPy computation is the culture-label diversity calculation.
Each matrix row contains the actual label counts for one group. I sum across
columns with axis one and keepdims, then divide by the row total. Broadcasting
turns those counts into probabilities without a Python loop over every value.

I calculate Shannon entropy as minus the sum of p times the natural log of p.
I also calculate the Gini-Simpson index as one minus the sum of squared
probabilities. The calculation is implemented with NumPy rather than a diversity
library. Zero probabilities contribute zero, so the code avoids evaluating log
of zero. A group with no documented labels is undefined, while a genuinely
single-label group has Shannon entropy zero.

These numbers summarize concentration in documented labels. They do not measure
how diverse an entire society was. NumPy also computes medians and quartiles
for the date question, and row-normalized proportions for the medium question.

## 7:00–8:30 — Q1: prediction and reveal

[Open Predict and compare. Give the audience about ten seconds, then select and reveal.]

Before I reveal the table, which department do you expect to have the earliest
median recorded begin year?

[Reveal the computed comparison.]

In this sample, Greek and Roman Art has the earliest median, 530 BCE. Asian Art
has a median of 1700 CE, and European Paintings has a median of 1760 CE. The
interquartile range describes the spread of the middle half of the records.
These are interval begin years, not exact creation dates. Removing very wide
date intervals preserves the median ordering but changes some spread comparisons,
so that part of the interpretation needs qualification.

## 8:30–10:00 — Q2: medium composition

[Click Painting media, choose Q2, and retain All medium groups.]

For the second question, each percentage uses the records in one department
and century as its denominator. This avoids treating a larger century group as
automatically more dominant. The main display requires at least twenty records;
smaller groups remain available in the output tables.

A clear contrast appears in European Paintings. Twenty-four of twenty-five
records in recorded century fourteen CE are classified as tempera, or 96 percent.
In century nineteen, 303 of 350 are classified as oil painting, or 86.6 percent.
This is a difference in the sampled catalog composition, not proof of a global
historical transition or its cause. The categories use documented keyword rules,
with the original medium text preserved for review.

## 10:00–11:30 — Q3: coverage and interaction

[Open Culture calculator. Select European Paintings, then Asian Art; toggle uncertainty.]

European Paintings demonstrates an important limitation: there are no documented
culture labels, so the indices are undefined. That is not zero cultural diversity.
For Asian Art, the Japan and China labels together account for 81.5 percent of
the whole department's documented sample. For Greek and Roman Art, Greek, Attic
and Roman together account for 66.5 percent of documented records.

The uncertainty toggle changes which labels enter the calculation. Different
departments use different vocabularies and levels of detail, so I do not rank
historical societies by the resulting index values. This calculator uses all
sampled objects in its department; the date-filtered explorer can have a different
denominator, which is stated on screen.

## 11:30–12:15 — Object interaction

[Open Object browser, search a visible title word, then select one result.]

The object browser connects the aggregate results to actual metadata. A user can
search a title or artist and select a matching object. The displayed details
come from the processed records. These examples are not claimed to be a
representative random subsample, and searching here does not change the analysis.

## 12:15–13:00 — Conclusion

The project demonstrates a reproducible workflow from API requests to cleaning,
question-driven analysis, and a useful interactive application. Its conclusions
are limited by the department sampling design, uncertain date ranges, coarse
medium rules, and uneven culture documentation. I checked sensitivity to wide
dates and uncertain labels. PyTorch was optional and unnecessary for these
questions. Thank you; I am happy to explain the data choices, calculations, or code.

## 13:00–15:00 — Questions

Do not read a prepared extra paragraph. Answer the question asked, and show the
relevant code/table. The [main guide](presentation_15min.md) includes likely questions
and concise evidence anchors. If the instructor shortens the slot, prioritize the acquisition, one pandas
operation, one numerical computation, and a clear result; shorten optional interactions.
