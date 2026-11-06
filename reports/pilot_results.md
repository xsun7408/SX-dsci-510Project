# Historical 300-record pilot

This is the earlier pilot checkpoint. See [full-sample results](full_sample_results.md)
for the subsequent 3,000-record analysis; do not combine their sample populations.

## Acquisition validation

- The 20-record smoke test completed with 20 successes and no missing IDs.
- The pilot completed with 300 successes, 100 per department, and no missing IDs.
- Re-running each acquisition used no network requests and left the cache unchanged.
- At that checkpoint, the shared cache contained 313 unique records because the
  20- and 300-record manifests were not nested samples.
- Four acquisition tests passed. Quality calculations were separately checked
  for manifest filtering, blank strings, missing IDs, and negative dates.

## Missing values

| Department | Records | culture | country | medium | artistNationality | Begin/end date fields |
|---|---:|---:|---:|---:|---:|---:|
| Asian Art | 100 | 0% | 100% | 0% | 70% | 0% |
| European Paintings | 100 | 100% | 100% | 0% | 0% | 0% |
| Greek and Roman Art | 100 | 3% | 100% | 0% | 100% | 0% |

Missing means absent, null, or blank; populated date fields are not necessarily
usable dates. There were 96 negative begin years, three zero begin years, 14
intervals wider than 500 years, and no reversed intervals. Objects 71838 and
71575 had blank descriptions with 0/0 bounds. Object 257827 had a BCE-to-CE
description with bounds 0 and 25, requiring different interpretation from a
simple unknown date.

## Request issue

The initial expanded pilot at a 0.25-second interval encountered consecutive
HTTP 403 responses and was stopped. A later diagnostic request returned 200;
the cause was not established. After increasing the default interval to one
second and adding a three-consecutive-403 stop rule, resumption completed using
the same IDs. No failed IDs were replaced, and proxy access was not bypassed.

The pilot established the acquisition workflow and exposed field coverage
limitations. It did not establish collection-wide cultural or temporal patterns.
