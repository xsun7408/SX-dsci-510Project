"""Summarize a saved sample's coverage without mixing in other cached samples."""
import argparse
import json
from pathlib import Path

import pandas as pd

from acquire import load_cache

FIELDS = ['culture', 'country', 'medium', 'artistNationality', 'objectBeginDate', 'objectEndDate']


def summarize(manifest_path):
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    cached = load_cache(manifest_path.parent / 'objects.jsonl')
    selected = manifest['objectIDs']
    records = [cached[i] for i in selected if i in cached]
    if not records:
        raise ValueError('No acquired records for this manifest')
    df = pd.DataFrame(records).replace(r'^\s*$', pd.NA, regex=True)
    missing = df.reindex(columns=FIELDS).isna()
    missing['department'] = df['department']
    percentages = missing.groupby('department')[FIELDS].mean().mul(100).round(1)
    counts = df.groupby('department').size().rename('records')
    table = pd.concat([counts, percentages.add_suffix('_missing_pct')], axis=1)
    dates = df.reindex(columns=['objectBeginDate', 'objectEndDate']).apply(pd.to_numeric, errors='coerce')
    summary = {
        'target': manifest['target'],
        'acquired': len(records),
        'missing_ids': [i for i in selected if i not in cached],
        'negative_begin_years': int(dates['objectBeginDate'].lt(0).sum()),
        'zero_begin_years': int(dates['objectBeginDate'].eq(0).sum()),
        'begin_after_end': int(dates['objectBeginDate'].gt(dates['objectEndDate']).sum()),
        'date_spans_over_500_years': int((dates['objectEndDate'] - dates['objectBeginDate']).gt(500).sum()),
        'note': 'Missing means absent/null/blank; zero dates are flagged separately, not treated as missing. Metadata includes both public-domain and other records.'
    }
    prefix = manifest_path.with_suffix('')
    table.to_csv(str(prefix) + '.quality.csv')
    Path(str(prefix) + '.quality.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(table.to_string())
    print(json.dumps(summary, indent=2))
    return table, summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    summarize(parser.parse_args().manifest)
