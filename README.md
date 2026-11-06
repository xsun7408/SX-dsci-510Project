# SX-dsci-510Project

Metropolitan Museum metadata analysis for DSCI 510.

## Step 1: API acquisition

Python 3.12 is available in the cloud environment. From this checkout:

```bash
python3 -m venv /workspace/met-venv
/workspace/met-venv/bin/python -m pip install -r requirements.txt
/workspace/met-venv/bin/python -m unittest discover -s tests -v
/workspace/met-venv/bin/python acquire.py --count 20
```

The default departments are European Paintings (11), Asian Art (6), and Greek
and Roman Art (13). The total count is split approximately equally among them.
After inspecting the pilot, use `--count 300` for a field-quality pilot and
`--count 3000` for the proposed full sample. Do not interpret equal departmental
sample sizes as the collection's department proportions.

- `get_departments`: retrieve department IDs and names.
- `get_object_ids`: retrieve candidate IDs for one department.
- `fetch_object`: retrieve and validate one metadata record.
- `iter_records`: yield cached records or fetch and immediately persist new ones.

`data/sample_COUNT_SEED.json` preserves selected IDs, the seed, department catalog,
and acquisition start time. Re-running the same command uses this manifest.
`data/objects.jsonl` stores raw records shared by all sample sizes. Existing IDs
are skipped; failed IDs can be retried by re-running the same command.
`data/sample_COUNT_SEED.result.json` reports successes and failed IDs;
`logs/acquire.log` records errors. Partial acquisition exits with code 1.
A malformed cache stops processing to avoid silently overwriting data.

Requests use a User-Agent, connection/read timeouts, and a 1-second minimum
interval. Network failures, 429, and selected transient server errors get bounded
exponential retries; numeric Retry-After values are respected. HTTP 403 is not
retried for the same ID automatically; three consecutive 403 responses stop the
run and preserve the cache. The default interval is conservative and can be
changed with `--interval`. A proxy CONNECT denial requires network configuration,
not a different User-Agent. There is no API key requirement.

Source: https://metmuseum.github.io/
API: https://collectionapi.metmuseum.org/public/collection/v1
Verify current source usage guidance before large runs. The sample includes
metadata irrespective of `isPublicDomain`; image licensing is a separate concern.

## Next checkpoint

After the pilot, inspect missing fields by department: culture, country, medium,
artistNationality, objectBeginDate, and objectEndDate. Choose analysis populations
separately for each question. No real acquisition or analysis results should be
claimed until the API run succeeds. The three automated tests use mocked responses,
not museum data, and validate recovery and request behavior only.

## Step 2: pilot field quality

After acquisition, calculate per-department missing percentages and date flags:

```bash
/workspace/met-venv/bin/python inspect_quality.py data/sample_300_510.json
```

The script uses only IDs from the selected manifest, even if the shared cache
contains other samples. It writes `.quality.csv` and `.quality.json` next to the
manifest. Empty and whitespace-only strings count as missing. Negative years,
zero begin years, reversed date intervals, and intervals exceeding 500 years are
reported separately; these flags do not automatically delete records.
